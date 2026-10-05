"""Deterministic difficulty progression.

The rule *proposes* a working level; it never decides what is allowed. Every proposal is
clamped to the clinician's range here and validated again by the issuer and the DB trigger.
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical.models import ConstraintSet
from app.performance.models import PerformanceProfile

RECENT_WINDOW = 20


def clamp(value: int, cs: ConstraintSet) -> int:
    return max(cs.min_difficulty, min(cs.max_difficulty, value))


async def get_profile(
    db: AsyncSession, patient_id: uuid.UUID, exercise_type: str, cs: ConstraintSet
) -> PerformanceProfile:
    profile = await db.get(PerformanceProfile, (patient_id, exercise_type))
    if profile is None:
        profile = PerformanceProfile(
            patient_id=patient_id,
            exercise_type=exercise_type,
            target_difficulty=cs.min_difficulty,
            consecutive_correct=0,
            consecutive_incorrect=0,
            total_attempts=0,
            total_correct=0,
            recent_outcomes=[],
        )
        db.add(profile)
    return profile


def apply_outcome(profile: PerformanceProfile, outcome: str, cs: ConstraintSet) -> None:
    profile.total_attempts += 1
    profile.recent_outcomes = [*profile.recent_outcomes, outcome][-RECENT_WINDOW:]
    level = profile.target_difficulty

    if outcome == "correct":
        profile.total_correct += 1
        profile.consecutive_correct += 1
        profile.consecutive_incorrect = 0
        if profile.consecutive_correct >= cs.advance_after_correct:
            level += 1
            profile.consecutive_correct = 0
    elif outcome == "near_miss":
        # Close attempts neither advance nor step back.
        profile.consecutive_correct = 0
        profile.consecutive_incorrect = 0
    else:
        profile.consecutive_incorrect += 1
        profile.consecutive_correct = 0
        if profile.consecutive_incorrect >= cs.step_back_after_incorrect:
            level -= 1
            profile.consecutive_incorrect = 0

    profile.target_difficulty = clamp(level, cs)
