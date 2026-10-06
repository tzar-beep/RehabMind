"""The only output shapes accepted from a provider (also sent to Ollama as JSON Schemas).

`extra="forbid"`: any field the application did not ask for (an image URL, free-text
reasoning, a score) makes the whole output invalid.
"""

import enum

from pydantic import BaseModel, ConfigDict, Field

from app.ai.prompts import EXERCISE_PROMPT_VERSION


class Rationale(enum.StrEnum):
    """Structured reason codes. The model never returns free-text reasoning."""

    REINFORCE_RECENT_ERROR = "reinforce_recent_error"
    CONSOLIDATE_SUCCESS = "consolidate_success"
    INTRODUCE_NEW = "introduce_new"
    CATEGORY_VARIETY = "category_variety"


class ExerciseOutput(BaseModel):
    """Use case 1. The model picks a catalogue stimulus by slug and writes the wording;
    image paths, answers and word banks always come from the catalogue."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stimulus_slug: str = Field(min_length=1, max_length=64)
    difficulty: int = Field(ge=1, le=5)
    prompt: str = Field(min_length=3, max_length=60)
    # Picture naming only (meaning hint, then first sound).
    semantic_cue: str | None = Field(default=None, min_length=3, max_length=80)
    phonemic_cue: str | None = Field(default=None, min_length=1, max_length=6)
    # Sentence construction and picture description only: one supportive hint.
    hint: str | None = Field(default=None, min_length=3, max_length=90)
    rationale: Rationale


PictureNamingOutput = ExerciseOutput  # backwards-compatible name
PROMPT_VERSION = EXERCISE_PROMPT_VERSION


class FeedbackOutput(BaseModel):
    """Use case 2: supportive feedback on an answer that is already scored."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    feedback: str = Field(min_length=3, max_length=200)
    optional_hint: str | None = Field(default=None, max_length=120)


class SummaryOutput(BaseModel):
    """Use case 3: a clinician-facing summary of recorded practice data."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    summary: str = Field(min_length=10, max_length=600)
    strengths: list[str] = Field(default_factory=list, max_length=2)
    focus_areas: list[str] = Field(default_factory=list, max_length=2)
