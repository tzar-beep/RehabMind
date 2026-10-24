"""Rule-based exercise proposals. The AI generator (app.ai.personalization) produces the same
`Proposal` contract; every proposal, whatever its source, goes through the issuer.

Stimuli come only from the curated catalogue (`stimuli` table). Real-world photos are
used throughout (no drawings): BOSS object photos for naming, Wikimedia scenes otherwise.
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
from app.exercises.types import CHOICE_TYPES, IMPLEMENTED_TYPES, ExerciseType, ResponseMode
from app.performance.progression import clamp

GENERATOR_VERSION = "rules-v2"
SUPPORTED_MODES = frozenset({ResponseMode.TEXT, ResponseMode.SPEECH})
RECENT_EXCLUDE = 30

DEFAULT_PROMPTS = {
    ExerciseType.PICTURE_NAMING: "What is this?",
    ExerciseType.PICTURE_DESCRIPTION: "Describe what you see in the picture.",
    ExerciseType.SENTENCE_CONSTRUCTION: "Build a sentence using these words.",
    ExerciseType.WORD_REPETITION: "Say this word.",
    ExerciseType.WORD_RECOGNITION: "Which picture shows this word?",
    # Sentence completion and category naming build their prompt from the picture's data.
}
# "Which one is ...?" for category naming, by semantic group (catalogue "group").
CATEGORY_QUESTIONS = {
    "animal": "an animal",
    "food": "something you can eat",
    "vehicle": "a vehicle",
    "tableware": "something you eat or drink with",
    "furniture": "furniture",
    "instrument": "a musical instrument",
    "tool": "a tool",
    "clothing": "something you wear",
    "plant": "a plant",
}
# Groups too close to use as each other's wrong answers (a tomato is food and a plant).
CLOSE_GROUPS = {
    "food": {"plant", "tableware"},
    "plant": {"food"},
    "tableware": {"food"},
}
CHOICES = 4
INSTRUCTIONS = {
    (ExerciseType.PICTURE_NAMING, True): "Say the word for this picture.",
    (ExerciseType.PICTURE_NAMING, False): "Type the word for this picture.",
    (ExerciseType.PICTURE_DESCRIPTION, True): "Say a few words about the picture.",
    (ExerciseType.PICTURE_DESCRIPTION, False): "Type a few words about the picture.",
    (ExerciseType.SENTENCE_CONSTRUCTION, True): "Say the sentence, using all the words.",
    (ExerciseType.SENTENCE_CONSTRUCTION, False): "Tap the words in the right order.",
    (ExerciseType.WORD_REPETITION, True): "Listen, then say the word.",
    (ExerciseType.WORD_REPETITION, False): "Read the word, then type it.",
    (ExerciseType.SENTENCE_COMPLETION, True): "Say the missing word.",
    (ExerciseType.SENTENCE_COMPLETION, False): "Type the missing word.",
    (ExerciseType.WORD_RECOGNITION, False): "Listen, then tap the right picture.",
    (ExerciseType.CATEGORY_NAMING, False): "Tap the picture that belongs.",
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


def allowed_modes(cs: ConstraintSet, exercise_type: str | None = None) -> list[str]:
    modes = [m for m in cs.allowed_response_modes if m in SUPPORTED_MODES]
    if exercise_type in CHOICE_TYPES:
        # A tapped choice is sent as text: the "typing or tapping" answer method.
        modes = [m for m in modes if m == ResponseMode.TEXT]
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
    options: list[Stimulus] | None = None,
) -> Proposal:
    """Exercise content for one approved stimulus. Image paths always come from the catalogue."""
    speech_first = ResponseMode.SPEECH in modes and (
        exercise_type != ExerciseType.SENTENCE_CONSTRUCTION or ResponseMode.TEXT not in modes
    )
    task = stim.task or {}
    if exercise_type == ExerciseType.SENTENCE_COMPLETION:
        prompt = task["cloze"]
    elif exercise_type == ExerciseType.CATEGORY_NAMING:
        prompt = f"Which one is {CATEGORY_QUESTIONS[task['group']]}?"
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
    elif exercise_type == ExerciseType.SENTENCE_COMPLETION:
        # Meaning, then first sound, as for naming; the picture stays as support.
        content["cues"] = cues if cues is not None else rule_cues(stim.category, stim.target)
        expected["accepted_answers"] = stim.accepted_answers
    elif exercise_type == ExerciseType.WORD_REPETITION:
        content["word"] = stim.target
        expected["accepted_answers"] = stim.accepted_answers
    elif exercise_type in CHOICE_TYPES:
        if not options or len(options) < 2:
            raise NoSafeExercise("not enough pictures to choose from")
        if exercise_type == ExerciseType.WORD_RECOGNITION:
            content["word"] = stim.target
        # The pictures are the answer choices; no picture above the question.
        content["image_url"] = None
        content["options"] = [{"word": o.target, "image_url": o.image_path} for o in options]
        expected["accepted_answers"] = [stim.target]
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


async def choice_options(db: AsyncSession, stim: Stimulus, exercise_type: str) -> list[Stimulus]:
    """The answer choices for a picture-choice exercise: the target and CHOICES - 1 others,
    in random order.

    Word recognition: one choice from the target's own group (a related distractor, as in
    word-picture matching tests) and the rest unrelated. Category naming: only pictures from
    clearly different groups, so exactly one choice belongs.
    """
    rows = await db.execute(
        select(Stimulus).where(
            Stimulus.is_active,
            any_(Stimulus.exercise_types) == ExerciseType.PICTURE_NAMING,
            Stimulus.id != stim.id,
        )
    )
    names = {stim.target.lower(), *(a.lower() for a in stim.accepted_answers)}
    pool = [s for s in rows.scalars() if s.target.lower() not in names]
    group = (stim.task or {}).get("group")
    rng = secrets.SystemRandom()
    if exercise_type == ExerciseType.CATEGORY_NAMING:
        avoid = {group, *CLOSE_GROUPS.get(group, set())}
        others = [s for s in pool if (s.task or {}).get("group") not in avoid | {None}]
        picked = rng.sample(others, min(CHOICES - 1, len(others)))
    else:
        related = [s for s in pool if group and (s.task or {}).get("group") == group]
        picked = rng.sample(related, 1) if related else []
        rest = [s for s in pool if s not in picked and (s.task or {}).get("group") != group]
        picked += rng.sample(rest, min(CHOICES - 1 - len(picked), len(rest)))
    options = [stim, *picked]
    rng.shuffle(options)
    return options


async def build_for(
    db: AsyncSession, exercise_type: str, stim: Stimulus, modes: list[str], source: str
) -> Proposal:
    """build(), fetching the answer choices first when the type needs them."""
    options = (
        await choice_options(db, stim, exercise_type) if exercise_type in CHOICE_TYPES else None
    )
    return build(exercise_type, stim, modes, source, options=options)


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
    modes = allowed_modes(cs, exercise_type)
    in_session, recent = await used_stimuli(db, patient_id, session_id)

    wanted = clamp(target_difficulty, cs)
    # Nearest difficulty first, staying inside the clinician's range.
    levels = sorted(range(cs.min_difficulty, cs.max_difficulty + 1), key=lambda d: abs(d - wanted))
    for exclude in (recent, in_session):
        for level in levels:
            if pool := await candidates_at(db, cs, level, exclude, exercise_type):
                stim = secrets.choice(prefer_photos(pool))
                return await build_for(db, exercise_type, stim, modes, "rule")
    raise NoSafeExercise("stimulus library exhausted")


async def fallback(
    db: AsyncSession,
    session_id: uuid.UUID,
    cs: ConstraintSet,
    exercise_type: str = ExerciseType.PICTURE_NAMING,
) -> Proposal:
    """Most conservative option: the clinician's minimum difficulty, nothing clever."""
    check_type(cs, exercise_type)
    modes = allowed_modes(cs, exercise_type)
    in_session = await session_stimuli(db, session_id)
    for exclude in (in_session, set()):
        if pool := await candidates_at(db, cs, cs.min_difficulty, exclude, exercise_type):
            stim = sorted(prefer_photos(pool), key=lambda s: s.slug)[0]
            return await build_for(db, exercise_type, stim, modes, "fallback")
    raise NoSafeExercise("no stimulus at minimum difficulty")
