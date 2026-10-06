"""AI-personalized exercises: a fixed, bounded pipeline (not an agent).

The application chooses the exercise type (deterministic rotation); the model only picks
one approved catalogue stimulus for it and words the prompt.

    build minimal input → provider.generate → schema → clinical → safety
        ├─ accept → Proposal(source="ai") → ExerciseIssuer (validates again) → DB trigger
        └─ reject → retry (max MAX_ATTEMPTS) → None → caller falls back to rules/fallback

Every attempt is written to `ai_generations`.
"""

import asyncio
import json
import time
import uuid
from collections import Counter
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models import AIGeneration
from app.ai.provider import AIProvider, AIProviderError, GenerationRequest
from app.ai.schemas import (
    PROMPT_VERSION,
    SYSTEM_PROMPT,
    USER_PROMPT_TEMPLATE,
    ExerciseOutput,
)
from app.clinical.models import ConstraintSet
from app.exercises.cues import phonemic_cue
from app.exercises.generator import (
    NoSafeExercise,
    Proposal,
    allowed_modes,
    build,
    candidates_at,
    prefer_photos,
    used_stimuli,
)
from app.exercises.models import Exercise, Stimulus
from app.exercises.types import ExerciseType
from app.performance.models import PerformanceProfile
from app.performance.progression import clamp
from app.sessions import resets
from app.sessions.models import ExerciseResponse, PracticeSession
from app.validation.exercise import check_clinical, check_safety, check_schema

TASK = "exercise.personalize"
MAX_ATTEMPTS = 2
TIMEOUT_S = 10
MAX_CANDIDATES = 12
RAW_OUTPUT_LIMIT = 4000


async def _category_stats(db: AsyncSession, patient_id: uuid.UUID) -> tuple[dict, dict]:
    rows = await db.execute(
        select(Stimulus.category, ExerciseResponse.outcome)
        .join(Exercise, Exercise.stimulus_id == Stimulus.id)
        .join(ExerciseResponse, ExerciseResponse.exercise_id == Exercise.id)
        .where(
            Exercise.patient_id == patient_id,
            resets.after(ExerciseResponse.created_at, await resets.cutoff(db, patient_id)),
        )
        .order_by(ExerciseResponse.created_at.desc())
        .limit(50)
    )
    totals, correct = Counter(), Counter()
    for category, outcome in rows.all():
        totals[category] += 1
        correct[category] += outcome == "correct"
    accuracy = {c: round(correct[c] / n, 2) for c, n in totals.items()}
    return accuracy, dict(totals)


async def build_input(
    db: AsyncSession,
    session: PracticeSession,
    cs: ConstraintSet,
    profile: PerformanceProfile,
    exercise_type: str = ExerciseType.PICTURE_NAMING,
) -> tuple[dict[str, Any], dict[str, Stimulus]]:
    """Data minimization: no names, emails, user/patient IDs or free text from the patient."""
    in_session, recent = await used_stimuli(db, session.patient_id, session.id)
    target = clamp(profile.target_difficulty, cs)
    pool = await candidates_at(db, cs, target, in_session, exercise_type)
    if not pool:
        for level in sorted(
            range(cs.min_difficulty, cs.max_difficulty + 1), key=lambda d: abs(d - target)
        ):
            if pool := await candidates_at(db, cs, level, in_session, exercise_type):
                break
    if not pool:
        raise NoSafeExercise("no candidates for AI personalization")
    # Real-world photos only when any exist at this level (drawings are the fallback),
    # unseen first.
    pool = sorted(prefer_photos(pool), key=lambda s: (s.id in recent, s.slug))
    pool = pool[:MAX_CANDIDATES]
    accuracy, counts = await _category_stats(db, session.patient_id)
    return {
        "exercise_type": str(exercise_type),
        "target_difficulty": target,
        "min_difficulty": cs.min_difficulty,
        "max_difficulty": cs.max_difficulty,
        "recent_outcomes": list(profile.recent_outcomes[-10:]),
        "category_accuracy": accuracy,
        "category_counts": counts,
        "candidates": [
            {
                "slug": s.slug,
                "target": s.target,
                "category": s.category,
                "difficulty": s.difficulty,
                "kind": s.kind,
                "seen": s.id in recent,
            }
            for s in pool
        ],
    }, {s.slug: s for s in pool}


def _request(inp: dict[str, Any]) -> GenerationRequest:
    return GenerationRequest(
        task=TASK,
        prompt_version=PROMPT_VERSION,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=USER_PROMPT_TEMPLATE.format(
            exercise_type=inp["exercise_type"],
            target_difficulty=inp["target_difficulty"],
            min_difficulty=inp["min_difficulty"],
            max_difficulty=inp["max_difficulty"],
            recent_outcomes=inp["recent_outcomes"],
            category_accuracy=json.dumps(inp["category_accuracy"]),
            candidates=json.dumps(inp["candidates"]),
        ),
        input=inp,
        output_schema=ExerciseOutput.model_json_schema(),
    )


def _proposal(
    out: ExerciseOutput, stim: Stimulus, cs: ConstraintSet, model: str, exercise_type: str
) -> Proposal:
    cues = None
    if exercise_type == ExerciseType.PICTURE_NAMING:
        # Cueing hierarchy: meaning first, then first sound.
        cues = [out.semantic_cue or "", phonemic_cue(out.phonemic_cue or "")]
    return build(
        exercise_type,
        stim,
        allowed_modes(cs),
        "ai",
        prompt=out.prompt,
        cues=cues,
        generator_version=f"{model}:{PROMPT_VERSION}",
    )


async def propose(
    db: AsyncSession,
    provider: AIProvider,
    session: PracticeSession,
    cs: ConstraintSet,
    profile: PerformanceProfile,
    position: int,
    exercise_type: str = ExerciseType.PICTURE_NAMING,
) -> tuple[Proposal | None, AIGeneration | None]:
    """Return an accepted proposal plus its (not yet persisted) audit row, or (None, None).

    Rejected attempts are persisted immediately. The accepted row is persisted by the caller
    only after the issuer has created the exercise, so it can reference the exercise.
    """
    inp, candidates = await build_input(db, session, cs, profile, exercise_type)
    request = _request(inp)

    for attempt in range(1, MAX_ATTEMPTS + 1):
        row = AIGeneration(
            patient_id=session.patient_id,
            session_id=session.id,
            exercise_position=position,
            task=TASK,
            attempt=attempt,
            provider=getattr(provider, "name", "unknown"),
            model="unknown",
            prompt_version=PROMPT_VERSION,
            constraint_set_id=cs.id,
            constraint_version=cs.version,
            input_snapshot=inp,
            reason_codes=[],
        )
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(provider.generate(request), TIMEOUT_S)
        except (AIProviderError, TimeoutError) as e:
            row.latency_ms = int((time.perf_counter() - started) * 1000)
            row.status, row.failed_stage = "error", "provider"
            row.reason_codes = ["timeout" if isinstance(e, TimeoutError) else "provider_error"]
            db.add(row)
            continue
        row.latency_ms = int((time.perf_counter() - started) * 1000)
        row.provider, row.model, row.model_version = (
            result.provider,
            result.model,
            result.model_version,
        )
        row.raw_output = result.raw_output[:RAW_OUTPUT_LIMIT]

        verdict = check_schema(result.raw_output)
        if verdict.ok and verdict.output:
            row.parsed_output = verdict.output.model_dump(mode="json")
            verdict = check_clinical(verdict.output, cs, candidates, exercise_type)
            if verdict.ok and verdict.output:
                verdict = check_safety(
                    verdict.output, candidates[verdict.output.stimulus_slug], exercise_type
                )

        if verdict.ok and verdict.output:
            row.status = "accepted"
            stim = candidates[verdict.output.stimulus_slug]
            return _proposal(verdict.output, stim, cs, result.model, exercise_type), row

        row.status, row.failed_stage, row.reason_codes = "rejected", verdict.stage, verdict.reasons
        db.add(row)

    await db.flush()
    return None, None
