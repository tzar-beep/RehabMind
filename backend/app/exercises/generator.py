"""Rule-based exercise proposals (Phase 2). Phase 4 adds an AI generator behind the same
`Proposal` contract; every proposal, whatever its source, goes through the issuer."""

import secrets
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical.models import ConstraintSet
from app.exercises.cues import rule_cues
from app.exercises.models import Exercise, Stimulus
from app.exercises.types import IMPLEMENTED_TYPES, ExerciseType, ResponseMode
from app.performance.progression import clamp

GENERATOR_VERSION = "rules-v1"
SUPPORTED_MODES = frozenset({ResponseMode.TEXT, ResponseMode.SPEECH})
RECENT_EXCLUDE = 30


class NoSafeExercise(Exception):
    """No exercise can be issued within the clinician's constraints."""


@dataclass
class Proposal:
    exercise_type: str
    difficulty: int
    response_modes: list[str]
    stimulus: Stimulus | None
    content: dict[str, Any]
    expected: dict[str, Any]
    source: str
    generator_version: str = GENERATOR_VERSION


def allowed_modes(cs: ConstraintSet) -> list[str]:
    modes = [m for m in cs.allowed_response_modes if m in SUPPORTED_MODES]
    if not modes:
        raise NoSafeExercise("no supported response mode allowed")
    return modes


def _picture_naming(stim: Stimulus, modes: list[str], source: str) -> Proposal:
    return Proposal(
        exercise_type=ExerciseType.PICTURE_NAMING,
        difficulty=stim.difficulty,
        response_modes=modes,
        stimulus=stim,
        content={
            "prompt": "What is this?",
            "instructions": "Say the word for this picture."
            if ResponseMode.SPEECH in modes
            else "Type the word for this picture.",
            "image_url": stim.image_path,
            "cues": rule_cues(stim.category, stim.target),
        },
        expected={"target": stim.target, "accepted_answers": stim.accepted_answers},
        source=source,
    )


async def candidates_at(
    db: AsyncSession, cs: ConstraintSet, difficulty: int, exclude: set[uuid.UUID]
) -> list[Stimulus]:
    stmt = select(Stimulus).where(Stimulus.is_active, Stimulus.difficulty == difficulty)
    if cs.allowed_categories:
        stmt = stmt.where(Stimulus.category.in_(cs.allowed_categories))
    return [s for s in (await db.execute(stmt)).scalars() if s.id not in exclude]


async def session_stimuli(db: AsyncSession, session_id: uuid.UUID) -> set[uuid.UUID]:
    rows = await db.execute(select(Exercise.stimulus_id).where(Exercise.session_id == session_id))
    return {r for r in rows.scalars() if r}


async def used_stimuli(
    db: AsyncSession, patient_id: uuid.UUID, session_id: uuid.UUID
) -> tuple[set[uuid.UUID], set[uuid.UUID]]:
    in_session = await session_stimuli(db, session_id)
    recent_rows = await db.execute(
        select(Exercise.stimulus_id)
        .where(Exercise.patient_id == patient_id)
        .order_by(Exercise.issued_at.desc())
        .limit(RECENT_EXCLUDE)
    )
    return in_session, in_session | {r for r in recent_rows.scalars() if r}


async def propose_next(
    db: AsyncSession,
    patient_id: uuid.UUID,
    session_id: uuid.UUID,
    cs: ConstraintSet,
    target_difficulty: int,
) -> Proposal:
    if ExerciseType.PICTURE_NAMING not in cs.allowed_exercise_types or not (
        IMPLEMENTED_TYPES & set(cs.allowed_exercise_types)
    ):
        raise NoSafeExercise("no implemented exercise type allowed")
    modes = allowed_modes(cs)
    in_session, recent = await used_stimuli(db, patient_id, session_id)

    wanted = clamp(target_difficulty, cs)
    # Nearest difficulty first, staying inside the clinician's range.
    levels = sorted(range(cs.min_difficulty, cs.max_difficulty + 1), key=lambda d: abs(d - wanted))
    for exclude in (recent, in_session):
        for level in levels:
            if pool := await candidates_at(db, cs, level, exclude):
                return _picture_naming(secrets.choice(pool), modes, "rule")
    raise NoSafeExercise("stimulus library exhausted")


async def fallback(db: AsyncSession, session_id: uuid.UUID, cs: ConstraintSet) -> Proposal:
    """Most conservative option: the clinician's minimum difficulty, nothing clever."""
    if ExerciseType.PICTURE_NAMING not in cs.allowed_exercise_types:
        raise NoSafeExercise("no implemented exercise type allowed")
    modes = allowed_modes(cs)
    in_session = await session_stimuli(db, session_id)
    for exclude in (in_session, set()):
        if pool := await candidates_at(db, cs, cs.min_difficulty, exclude):
            return _picture_naming(sorted(pool, key=lambda s: s.slug)[0], modes, "fallback")
    raise NoSafeExercise("no stimulus at minimum difficulty")
