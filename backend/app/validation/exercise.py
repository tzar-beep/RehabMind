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

from app.ai.schemas import PictureNamingOutput
from app.analysis.scoring import normalize
from app.clinical.models import ConstraintSet
from app.exercises.models import Stimulus


@dataclass
class Verdict:
    ok: bool
    stage: str | None = None
    reasons: list[str] = field(default_factory=list)
    output: PictureNamingOutput | None = None


# Medical/diagnostic/prognostic claims, pressure, and anything that is not exercise content.
_UNSAFE_PATTERNS = {
    "medical_claim": r"\b(brain|heal|healing|cure|recover(y|ing)?|diagnos\w*|therapy|"
    r"treatment|medic\w*|doctor|stroke|aphasia|damage|neuro\w*)\b",
    "pressure_language": r"\b(must|should have|wrong again|failed|fail)\b",
    "link_or_contact": r"(https?://|www\.|@[a-z]|\.com\b)",
    "digits": r"\d",
}
MAX_PROMPT_WORDS = 8
MAX_CUE_WORDS = 12


def check_schema(raw: str) -> Verdict:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return Verdict(False, "schema", ["invalid_json"])
    if not isinstance(data, dict):
        return Verdict(False, "schema", ["not_an_object"])
    try:
        return Verdict(True, output=PictureNamingOutput.model_validate(data))
    except ValidationError as e:
        codes = sorted({f"{err['type']}:{'.'.join(map(str, err['loc']))}" for err in e.errors()})
        return Verdict(False, "schema", codes)


def check_clinical(
    out: PictureNamingOutput, cs: ConstraintSet, candidates: dict[str, Stimulus]
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
    if not cs.min_difficulty <= out.difficulty <= cs.max_difficulty:
        reasons.append("difficulty_out_of_range")
    return Verdict(not reasons, None if not reasons else "clinical", reasons, out)


def check_safety(out: PictureNamingOutput, stim: Stimulus) -> Verdict:
    reasons: list[str] = []
    answers = [normalize(a) for a in stim.accepted_answers]
    for name, text, max_words in (
        ("prompt", out.prompt, MAX_PROMPT_WORDS),
        ("semantic_cue", out.semantic_cue, MAX_CUE_WORDS),
    ):
        norm = f" {normalize(text)} "
        if any(f" {a} " in norm or f" {a}s " in norm for a in answers):
            reasons.append(f"answer_leak:{name}")
        if len(text.split()) > max_words:
            reasons.append(f"too_long:{name}")
        for code, pattern in _UNSAFE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                reasons.append(f"{code}:{name}")
    cue = out.phonemic_cue.lower()
    if (
        not cue.isalpha()
        or not normalize(stim.target).startswith(cue)
        or len(cue) >= len(stim.target)
    ):
        reasons.append("invalid_phonemic_cue")
    return Verdict(not reasons, None if not reasons else "safety", reasons, out)
