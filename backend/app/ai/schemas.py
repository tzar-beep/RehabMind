import enum

from pydantic import BaseModel, ConfigDict, Field


class Rationale(enum.StrEnum):
    """Structured reason codes. The model never returns free-text reasoning."""

    REINFORCE_RECENT_ERROR = "reinforce_recent_error"
    CONSOLIDATE_SUCCESS = "consolidate_success"
    INTRODUCE_NEW = "introduce_new"
    CATEGORY_VARIETY = "category_variety"


class PictureNamingOutput(BaseModel):
    """The only shape accepted from a provider for picture-naming personalization."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    stimulus_slug: str = Field(min_length=1, max_length=64)
    difficulty: int = Field(ge=1, le=5)
    prompt: str = Field(min_length=3, max_length=60)
    semantic_cue: str = Field(min_length=3, max_length=80)
    phonemic_cue: str = Field(min_length=1, max_length=6)
    rationale: Rationale


PROMPT_VERSION = "picture-naming-v1"

SYSTEM_PROMPT = """You personalize one picture-naming exercise for an adult practising word \
finding after stroke. Choose exactly one stimulus from CANDIDATES. Write a short, plain, \
respectful question (max 8 words) that does not contain the target word, a semantic cue \
(category or use, max 12 words, must not contain the target word) and a phonemic cue \
(the first 1-3 letters of the target word). Never give medical advice, diagnoses, \
predictions about recovery, or praise that makes clinical claims. Return only JSON matching \
the schema, including one rationale code."""

USER_PROMPT_TEMPLATE = """TARGET_DIFFICULTY: {target_difficulty}
ALLOWED_DIFFICULTY: {min_difficulty}-{max_difficulty}
RECENT_OUTCOMES (oldest first): {recent_outcomes}
CATEGORY_ACCURACY: {category_accuracy}
CANDIDATES: {candidates}"""
