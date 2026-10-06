"""Rule-based exercise proposals. The AI generator (app.ai.personalization) produces the same
`Proposal` contract; every proposal, whatever its source, goes through the issuer.

Stimuli come only from the curated catalogue (`stimuli` table). Real-world photos are
preferred; Lucide line drawings remain as the fallback for picture naming.
"""

import secrets
import uuid
from dataclasses import dataclass
from typing import Any

from sqlalchemy import any_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical.models import ConstraintSet
from app.exercises.cues import rule_cues
from app.exercises.models import Exercise, Stimulus
from app.exercises.types import IMPLEMENTED_TYPES, ExerciseType, ResponseMode
from app.performance.progression import clamp

GENERATOR_VERSION = "rules-v2"
SUPPORTED_MODES = frozenset({ResponseMode.TEXT, ResponseMode.SPEECH})
RECENT_EXCLUDE = 30

DEFAULT_PROMPTS = {
    ExerciseType.PICTURE_NAMING: "What is this?",
    ExerciseType.PICTURE_DESCRIPTION: "Describe what you see in the picture.",
    ExerciseType.SENTENCE_CONSTRUCTION: "Build a sentence using these words.",
}
INSTRUCTIONS = {
    (ExerciseType.PICTURE_NAMING, True): "Say the word for this picture.",
    (ExerciseType.PICTURE_NAMING, False): "Type the word for this picture.",
    (ExerciseType.PICTURE_DESCRIPTION, True): "Say a few words about the picture.",
    (ExerciseType.PICTURE_DESCRIPTION, False): "Type a few words about the picture.",
    (ExerciseType.SENTENCE_CONSTRUCTION, True): "Say the sentence, using all the words.",
    (ExerciseType.SENTENCE_CONSTRUCTION, False): "Tap the words in the right order.",
}


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


def scrambled(words: list[str]) -> list[str]:
    """Deterministic word-bank order that never shows the sentence already in order."""
    shuffled = sorted(words, key=str.lower)
    return shuffled if shuffled != words else list(reversed(words))


def build(
    exercise_type: str,
    stim: Stimulus,
    modes: list[str],
    source: str,
    *,
    prompt: str | None = None,
    cues: list[str] | None = None,
    generator_version: str = GENERATOR_VERSION,
) -> Proposal:
    """Exercise content for one approved stimulus. Image paths always come from the catalogue."""
    speech_first = ResponseMode.SPEECH in modes and (
        exercise_type != ExerciseType.SENTENCE_CONSTRUCTION or ResponseMode.TEXT not in modes
    )
    content: dict[str, Any] = {
        "prompt": prompt or DEFAULT_PROMPTS[exercise_type],
        "instructions": INSTRUCTIONS[(exercise_type, speech_first)],
        "image_url": stim.image_path,
        "image_kind": stim.kind,
        "cues": [],
    }
    expected: dict[str, Any] = {"target": stim.target}
    if exercise_type == ExerciseType.PICTURE_NAMING:
        content["cues"] = cues if cues is not None else rule_cues(stim.category, stim.target)
        expected["accepted_answers"] = stim.accepted_answers
    elif exercise_type == ExerciseType.PICTURE_DESCRIPTION:
        expected["concepts"] = stim.task["description"]["concepts"]
    elif exercise_type == ExerciseType.SENTENCE_CONSTRUCTION:
        content["words"] = scrambled(stim.task["sentence"]["words"])
        expected["accepted_answers"] = stim.accepted_answers
    else:  # pragma: no cover - guarded by IMPLEMENTED_TYPES
        raise NoSafeExercise(f"{exercise_type} is not implemented")
    if exercise_type != ExerciseType.PICTURE_NAMING and cues:
        content["cues"] = cues  # one AI-written hint (validated before it gets here)
    return Proposal(
        exercise_type=exercise_type,
        difficulty=stim.difficulty,
        response_modes=modes,
        stimulus=stim,
        content=content,
        expected=expected,
        source=source,
        generator_version=generator_version,
    )


async def candidates_at(
    db: AsyncSession,
    cs: ConstraintSet,
    difficulty: int,
    exclude: set[uuid.UUID],
    exercise_type: str = ExerciseType.PICTURE_NAMING,
) -> list[Stimulus]:
    stmt = select(Stimulus).where(
        Stimulus.is_active,
        Stimulus.difficulty == difficulty,
        any_(Stimulus.exercise_types) == exercise_type,
    )
    if cs.allowed_categories:
        stmt = stmt.where(Stimulus.category.in_(cs.allowed_categories))
    return [s for s in (await db.execute(stmt)).scalars() if s.id not in exclude]


def prefer_photos(pool: list[Stimulus]) -> list[Stimulus]:
    return [s for s in pool if s.kind == "photo"] or pool


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


def check_type(cs: ConstraintSet, exercise_type: str) -> None:
    if exercise_type not in cs.allowed_exercise_types or exercise_type not in IMPLEMENTED_TYPES:
        raise NoSafeExercise(f"{exercise_type} not allowed or not implemented")


async def propose_next(
    db: AsyncSession,
    patient_id: uuid.UUID,
    session_id: uuid.UUID,
    cs: ConstraintSet,
    target_difficulty: int,
    exercise_type: str = ExerciseType.PICTURE_NAMING,
) -> Proposal:
    check_type(cs, exercise_type)
    modes = allowed_modes(cs)
    in_session, recent = await used_stimuli(db, patient_id, session_id)

    wanted = clamp(target_difficulty, cs)
    # Nearest difficulty first, staying inside the clinician's range.
    levels = sorted(range(cs.min_difficulty, cs.max_difficulty + 1), key=lambda d: abs(d - wanted))
    for exclude in (recent, in_session):
        for level in levels:
            if pool := await candidates_at(db, cs, level, exclude, exercise_type):
                return build(exercise_type, secrets.choice(prefer_photos(pool)), modes, "rule")
    raise NoSafeExercise("stimulus library exhausted")


async def fallback(
    db: AsyncSession,
    session_id: uuid.UUID,
    cs: ConstraintSet,
    exercise_type: str = ExerciseType.PICTURE_NAMING,
) -> Proposal:
    """Most conservative option: the clinician's minimum difficulty, nothing clever."""
    check_type(cs, exercise_type)
    modes = allowed_modes(cs)
    in_session = await session_stimuli(db, session_id)
    for exclude in (in_session, set()):
        if pool := await candidates_at(db, cs, cs.min_difficulty, exclude, exercise_type):
            stim = sorted(prefer_photos(pool), key=lambda s: s.slug)[0]
            return build(exercise_type, stim, modes, "fallback")
    raise NoSafeExercise("no stimulus at minimum difficulty")
