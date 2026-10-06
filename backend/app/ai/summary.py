"""AI progress summary for clinicians (GenAI use case 3).

    recorded answers since the latest fresh start → per-objective figures (counts, accuracy,
    learned-model trend) → versioned prompt → LLM → validation (no invented numbers, no
    diagnosis) → draft summary for the clinician

Clinician-facing only, on request. If the model is unavailable or its output fails
validation, a plain rule-based summary of the same figures is returned instead, labelled as
such. Figures describe recorded practice, not a clinical assessment.
"""

import uuid
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models import AIGeneration
from app.ai.prompts import SUMMARY_PROMPT_VERSION, inline_schema, summary_prompts
from app.ai.provider import AIProvider, GenerationRequest
from app.ai.runner import generate_validated
from app.ai.schemas import SummaryOutput
from app.clinical.models import ConstraintSet
from app.exercises.models import Exercise
from app.exercises.types import OBJECTIVE_LABELS, OBJECTIVES, Objective
from app.performance import ability
from app.sessions import resets
from app.sessions.models import ExerciseResponse, PracticeSession
from app.validation.generated_text import check_summary

TASK = "progress.summarize"
_EXERCISE_FOR = {objective: exercise for exercise, objective in OBJECTIVES.items()}


async def build_input(db: AsyncSession, patient_id: uuid.UUID) -> dict[str, Any]:
    reset_at = await resets.cutoff(db, patient_id)
    counts = {
        (t, o): n
        for t, o, n in (
            await db.execute(
                select(Exercise.exercise_type, ExerciseResponse.outcome, func.count())
                .join(Exercise, Exercise.id == ExerciseResponse.exercise_id)
                .where(
                    ExerciseResponse.patient_id == patient_id,
                    resets.after(ExerciseResponse.created_at, reset_at),
                )
                .group_by(Exercise.exercise_type, ExerciseResponse.outcome)
            )
        ).all()
    }
    sessions = await db.scalar(
        select(func.count())
        .select_from(PracticeSession)
        .where(
            PracticeSession.patient_id == patient_id,
            PracticeSession.status == "completed",
            resets.after(PracticeSession.started_at, reset_at),
        )
    )
    estimates = await ability.estimates(db, patient_id)
    objectives = []
    for objective in Objective:
        exercise = _EXERCISE_FOR[objective]
        answers = sum(n for (t, _), n in counts.items() if t == exercise)
        correct = counts.get((exercise, "correct"), 0)
        objectives.append(
            {
                "objective": objective.value,
                "label": OBJECTIVE_LABELS[objective].removeprefix("Improve ").capitalize(),
                "exercise": exercise.replace("_", " "),
                "answers": answers,
                "percent_correct": round(100 * correct / answers) if answers else 0,
                "trend": estimates[objective.value].trend.replace("_", " "),
            }
        )
    period = (
        f"since the fresh start on {reset_at:%d %B %Y}" if reset_at else "all recorded practice"
    )
    return {"period": period, "sessions_completed": sessions or 0, "objectives": objectives}


def build_request(inp: dict[str, Any]) -> GenerationRequest:
    system, user = summary_prompts(inp)
    return GenerationRequest(
        task=TASK,
        prompt_version=SUMMARY_PROMPT_VERSION,
        system_prompt=system,
        user_prompt=user,
        input=inp,
        output_schema=inline_schema(SummaryOutput.model_json_schema()),
    )


def rule_summary(inp: dict[str, Any]) -> SummaryOutput:
    """Non-AI fallback: the same figures, stated plainly."""
    practised = [o for o in inp["objectives"] if o["answers"]]
    if not practised:
        return SummaryOutput(summary="No answers have been recorded yet for this period.")
    parts = [
        f"{o['label']}: {o['answers']} answers, {o['percent_correct']}% correct ({o['trend']})."
        for o in practised
    ]
    best = max(practised, key=lambda o: o["percent_correct"])
    weakest = min(practised, key=lambda o: o["percent_correct"])
    return SummaryOutput(
        summary=f"{inp['sessions_completed']} sessions completed {inp['period']}. "
        + " ".join(parts),
        strengths=[f"{best['label']} has the highest share of correct answers."],
        focus_areas=[f"{weakest['label']} has the lowest share of correct answers."]
        if weakest is not best
        else [],
    )


async def summarize(
    db: AsyncSession, provider: AIProvider | None, patient_id: uuid.UUID, cs: ConstraintSet
) -> tuple[SummaryOutput, AIGeneration | None, dict[str, Any]]:
    """(summary, accepted AI row or None when the rule-based fallback was used, input)."""
    inp = await build_input(db, patient_id)
    out, row = None, None
    if provider is not None and any(o["answers"] for o in inp["objectives"]):
        out, row = await generate_validated(
            db,
            provider,
            build_request(inp),
            lambda raw: check_summary(raw, inp),
            patient_id=patient_id,
            constraint_set_id=cs.id,
            constraint_version=cs.version,
        )
        await db.commit()
    return (out or rule_summary(inp)), row, inp


async def latest(db: AsyncSession, patient_id: uuid.UUID) -> AIGeneration | None:
    return await db.scalar(
        select(AIGeneration)
        .where(
            AIGeneration.patient_id == patient_id,
            AIGeneration.task == TASK,
            AIGeneration.status == "accepted",
        )
        .order_by(AIGeneration.created_at.desc())
        .limit(1)
    )
