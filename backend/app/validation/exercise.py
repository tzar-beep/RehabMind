"""Validation of AI-generated exercise content. Pure functions, deterministic, no AI.

Stages run in order; the first failing stage rejects the output with reason codes.
  1. schema    — parseable JSON in the exact expected shape
  2. clinical  — consistent with the clinician's constraint set and the curated library
  3. safety    — patient-facing text is plain, respectful, non-medical, and does not leak
The ExerciseIssuer and the DB trigger re-check clinical rules independently afterwards.
"""

import json
import re
from dataclasses import dataclass, field

from pydantic import ValidationError

from app.ai.schemas import ExerciseOutput
from app.analysis.scoring import normalize
from app.clinical.models import ConstraintSet
from app.exercises.models import Stimulus


@dataclass
class Verdict:
    ok: bool
    stage: str | None = None
    reasons: list[str] = field(default_factory=list)
    output: ExerciseOutput | None = None


# Medical/diagnostic/prognostic claims, pressure, and anything that is not exercise content.
_UNSAFE_PATTERNS = {
    "medical_claim": r"\b(brain|heal|healing|cure|recover(y|ing)?|diagnos\w*|therapy|"
    r"treatment|medic\w*|doctor|stroke|aphasia|damage|neuro\w*)\b",
    "pressure_language": r"\b(must|should have|wrong again|failed|fail)\b",
    "link_or_contact": r"(https?://|www\.|@[a-z]|\.com\b)",
    "digits": r"\d",
}


def _words(text: str) -> str:
    """Normalized text with possessives removed ("dog's" -> "dog"), for leak checks."""
    return re.sub(r"'s(?![a-z])", "", normalize(text))


MAX_PROMPT_WORDS = 8
MAX_CUE_WORDS = 12
# A sentence hint may give a start ("Start with 'The dog...'") but not the sentence itself.
_FUNCTION_WORDS = {"the", "a", "an", "is", "are", "was", "were", "and", "to", "of", "in", "on"}
MAX_SENTENCE_WORDS_IN_HINT = 1


def check_schema(raw: str) -> Verdict:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return Verdict(False, "schema", ["invalid_json"])
    if not isinstance(data, dict):
        return Verdict(False, "schema", ["not_an_object"])
    try:
        return Verdict(True, output=ExerciseOutput.model_validate(data))
    except ValidationError as e:
        codes = sorted({f"{err['type']}:{'.'.join(map(str, err['loc']))}" for err in e.errors()})
        return Verdict(False, "schema", codes)


def check_clinical(
    out: ExerciseOutput,
    cs: ConstraintSet,
    candidates: dict[str, Stimulus],
    exercise_type: str = "picture_naming",
) -> Verdict:
    reasons: list[str] = []
    stim = candidates.get(out.stimulus_slug)
    if stim is None:
        reasons.append("stimulus_not_in_candidates")
    else:
        if stim.difficulty != out.difficulty:
            reasons.append("difficulty_mismatch")
        if cs.allowed_categories and stim.category not in cs.allowed_categories:
            reasons.append("category_not_allowed")
        if exercise_type not in stim.exercise_types:
            reasons.append("stimulus_not_for_exercise_type")
    if not cs.min_difficulty <= out.difficulty <= cs.max_difficulty:
        reasons.append("difficulty_out_of_range")
    return Verdict(not reasons, None if not reasons else "clinical", reasons, out)


def _leak_terms(stim: Stimulus, exercise_type: str) -> list[str]:
    if exercise_type == "picture_description":
        return [normalize(c["name"]) for c in stim.task["description"]["concepts"]]
    if exercise_type == "sentence_construction":
        return [normalize(stim.target)]
    return [normalize(a) for a in stim.accepted_answers]


def check_safety(
    out: ExerciseOutput, stim: Stimulus, exercise_type: str = "picture_naming"
) -> Verdict:
    reasons: list[str] = []
    answers = _leak_terms(stim, exercise_type)
    texts = [("prompt", out.prompt, MAX_PROMPT_WORDS)]
    if out.semantic_cue:
        texts.append(("semantic_cue", out.semantic_cue, MAX_CUE_WORDS))
    if out.hint:
        texts.append(("hint", out.hint, MAX_CUE_WORDS))
    for name, text, max_words in texts:
        norm = f" {_words(text)} "
        if any(f" {a} " in norm or f" {a}s " in norm for a in answers):
            reasons.append(f"answer_leak:{name}")
        if len(text.split()) > max_words:
            reasons.append(f"too_long:{name}")
        for code, pattern in _UNSAFE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                reasons.append(f"{code}:{name}")
    if exercise_type == "picture_naming":
        cue = (out.phonemic_cue or "").lower()
        if out.hint:
            reasons.append("unexpected_hint")
        if not out.semantic_cue or not cue:
            reasons.append("missing_cue")
        elif (
            not cue.isalpha()
            or not normalize(stim.target).startswith(cue)
            or len(cue) >= len(stim.target)
        ):
            reasons.append("invalid_phonemic_cue")
    else:
        if out.semantic_cue or out.phonemic_cue:
            reasons.append("unexpected_cue")
        if out.hint and exercise_type == "sentence_construction":
            content = set(normalize(stim.target).split()) - _FUNCTION_WORDS
            used = content & set(_words(out.hint).split())
            if len(used) > MAX_SENTENCE_WORDS_IN_HINT:
                reasons.append("answer_leak:hint")
    reasons = list(dict.fromkeys(reasons))
    return Verdict(not reasons, None if not reasons else "safety", reasons, out)
