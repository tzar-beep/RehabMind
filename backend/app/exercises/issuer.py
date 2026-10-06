"""ExerciseIssuer: the only code path that creates `Exercise` rows.

Validates every proposal (rule-based, fallback, or — from Phase 4 — AI-generated) against
the patient's latest clinical constraint set. The DB trigger re-checks the same invariants.
"""

from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical.models import ConstraintSet
from app.exercises.generator import Proposal
from app.exercises.models import Exercise
from app.exercises.types import IMPLEMENTED_TYPES
from app.sessions.models import PracticeSession


class ConstraintViolation(Exception):
    def __init__(self, reasons: list[str]) -> None:
        super().__init__(", ".join(reasons))
        self.reasons = reasons


def validate(p: Proposal, cs: ConstraintSet, session: PracticeSession, position: int) -> list[str]:
    """Return reason codes for every violated rule (empty list = valid)."""
    reasons: list[str] = []
    if p.exercise_type not in cs.allowed_exercise_types:
        reasons.append("type_not_allowed")
    if p.exercise_type not in IMPLEMENTED_TYPES:
        reasons.append("type_not_implemented")
    if not cs.min_difficulty <= p.difficulty <= cs.max_difficulty:
        reasons.append("difficulty_out_of_range")
    if not p.response_modes or not set(p.response_modes) <= set(cs.allowed_response_modes):
        reasons.append("response_mode_not_allowed")
    if p.stimulus is not None:
        if not p.stimulus.is_active:
            reasons.append("stimulus_inactive")
        if p.exercise_type not in p.stimulus.exercise_types:
            reasons.append("stimulus_not_for_exercise_type")
        if p.stimulus.difficulty != p.difficulty:
            reasons.append("stimulus_difficulty_mismatch")
        if cs.allowed_categories and p.stimulus.category not in cs.allowed_categories:
            reasons.append("category_not_allowed")
    if position > min(session.planned_exercises, cs.max_exercises_per_session):
        reasons.append("session_limit_reached")
    if cs.patient_id != session.patient_id:
        reasons.append("constraint_patient_mismatch")
    return reasons


async def issue(
    db: AsyncSession, session: PracticeSession, cs: ConstraintSet, p: Proposal, position: int
) -> Exercise:
    if reasons := validate(p, cs, session, position):
        raise ConstraintViolation(reasons)
    exercise = Exercise(
        session_id=session.id,
        patient_id=session.patient_id,
        constraint_set_id=cs.id,
        position=position,
        exercise_type=p.exercise_type,
        difficulty=p.difficulty,
        response_modes=p.response_modes,
        stimulus_id=p.stimulus.id if p.stimulus else None,
        content=p.content,
        expected=p.expected,
        source=p.source,
        generator_version=p.generator_version,
        status="pending",
    )
    db.add(exercise)
    await db.flush()
    return exercise
