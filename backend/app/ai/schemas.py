import enum

from pydantic import BaseModel, ConfigDict, Field


class Rationale(enum.StrEnum):
    """Structured reason codes. The model never returns free-text reasoning."""

    REINFORCE_RECENT_ERROR = "reinforce_recent_error"
    CONSOLIDATE_SUCCESS = "consolidate_success"
    INTRODUCE_NEW = "introduce_new"
    CATEGORY_VARIETY = "category_variety"


class ExerciseOutput(BaseModel):
    """The only shape accepted from a provider. The model picks a catalogue stimulus by slug
    and words the prompt; image paths and answers always come from the catalogue."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stimulus_slug: str = Field(min_length=1, max_length=64)
    difficulty: int = Field(ge=1, le=5)
    prompt: str = Field(min_length=3, max_length=60)
    # Picture naming only (meaning hint, then first sound). Omitted for other types.
    semantic_cue: str | None = Field(default=None, min_length=3, max_length=80)
    phonemic_cue: str | None = Field(default=None, min_length=1, max_length=6)
    rationale: Rationale


PictureNamingOutput = ExerciseOutput  # backwards-compatible name


PROMPT_VERSION = "exercise-v2"

SYSTEM_PROMPT = """You personalize one language exercise of type EXERCISE_TYPE for an adult \
practising after stroke. Choose exactly one stimulus from CANDIDATES (by slug; never invent \
images or words). Write a short, plain, respectful prompt (max 8 words) that does not reveal \
the answer. For picture_naming only, also give a semantic cue (category or use, max 12 \
words, must not contain the target word) and a phonemic cue (the first 1-3 letters of the \
target word); omit cues for other types. Never give medical advice, diagnoses, \
predictions about recovery, or praise that makes clinical claims. Return only JSON matching \
the schema, including one rationale code."""

USER_PROMPT_TEMPLATE = """EXERCISE_TYPE: {exercise_type}
TARGET_DIFFICULTY: {target_difficulty}
ALLOWED_DIFFICULTY: {min_difficulty}-{max_difficulty}
RECENT_OUTCOMES (oldest first): {recent_outcomes}
CATEGORY_ACCURACY: {category_accuracy}
CANDIDATES: {candidates}"""
