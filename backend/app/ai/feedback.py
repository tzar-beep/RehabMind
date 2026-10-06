"""AI feedback on a scored answer (GenAI use case 2).

    answer → deterministic score + analysis (final, unchanged)
        → structured context → versioned prompt → LLM → validation → short supportive tip

The score is decided before the model is asked and is never written back: the model only
explains it kindly. Generated once per exercise (cached in `ai_generations`); if no valid
feedback comes back, the patient simply keeps the standard feedback they already see.
"""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models import AIGeneration
from app.ai.prompts import (
    FEEDBACK_PROMPT_VERSION,
    describe_analysis,
    feedback_prompts,
    inline_schema,
)
from app.ai.provider import AIProvider, GenerationRequest
from app.ai.runner import MAX_ATTEMPTS, generate_validated
from app.ai.schemas import FeedbackOutput
from app.clinical.models import ConstraintSet
from app.exercises.models import Exercise
from app.exercises.types import OBJECTIVE_LABELS, OBJECTIVES, TARGET_SKILLS
from app.sessions.models import ExerciseResponse
from app.validation.generated_text import check_feedback

TASK = "feedback.generate"


def build_input(exercise: Exercise, response: ExerciseResponse) -> dict[str, Any]:
    """The answer and the scorer's findings. No names, emails or IDs."""
    objective = OBJECTIVES[exercise.exercise_type]
    return {
        "objective": objective.value,
        "objective_label": OBJECTIVE_LABELS[objective],
        "target_skill": TARGET_SKILLS[objective],
        "exercise_type": exercise.exercise_type,
        "difficulty": exercise.difficulty,
        "target": exercise.expected["target"],
        "response": (response.text or "")[:200] or "(no answer)",
        "mode": response.mode,
        "outcome": response.outcome,
        "score": response.score,
        "hints_used": response.analysis.get("hints_used", 0),
        "analysis": describe_analysis(exercise.exercise_type, response.analysis),
    }


def build_request(inp: dict[str, Any]) -> GenerationRequest:
    system, user = feedback_prompts(inp)
    return GenerationRequest(
        task=TASK,
        prompt_version=FEEDBACK_PROMPT_VERSION,
        system_prompt=system,
        user_prompt=user,
        input=inp,
        output_schema=inline_schema(FeedbackOutput.model_json_schema()),
    )


async def feedback_for(
    db: AsyncSession, provider: AIProvider, exercise: Exercise, response: ExerciseResponse
) -> FeedbackOutput | None:
    previous = (
        (
            await db.execute(
                select(AIGeneration).where(
                    AIGeneration.exercise_id == exercise.id, AIGeneration.task == TASK
                )
            )
        )
        .scalars()
        .all()
    )
    if accepted := next((g for g in previous if g.status == "accepted"), None):
        return FeedbackOutput.model_validate(accepted.parsed_output)
    if len(previous) >= MAX_ATTEMPTS:
        return None  # already tried and failed for this answer: don't keep calling

    inp = build_input(exercise, response)
    out, _ = await generate_validated(
        db,
        provider,
        build_request(inp),
        lambda raw: check_feedback(raw, response.outcome),
        patient_id=exercise.patient_id,
        constraint_set_id=exercise.constraint_set_id,
        constraint_version=await _constraint_version(db, exercise),
        session_id=exercise.session_id,
        exercise_id=exercise.id,
        exercise_position=exercise.position,
    )
    await db.commit()
    return out


async def _constraint_version(db: AsyncSession, exercise: Exercise) -> int:
    return await db.scalar(
        select(ConstraintSet.version).where(ConstraintSet.id == exercise.constraint_set_id)
    )
