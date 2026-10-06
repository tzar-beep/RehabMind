"""Validation of AI-written feedback (use case 2) and progress summaries (use case 3).

Same stages and the same `Verdict` as exercise validation (app.validation.exercise):
  1. schema   — parseable JSON in the exact expected shape
  2. safety   — no medical/diagnostic content, no pressure, no links; for patients no numbers
                (a number could look like a score); feedback never contradicts the official
                deterministic outcome; summaries never contain numbers that are not in the data
Pure functions, deterministic, no AI.
"""

import json
import re
from typing import Any

from pydantic import BaseModel, ValidationError

from app.ai.schemas import FeedbackOutput, SummaryOutput
from app.validation.exercise import _UNSAFE_PATTERNS, Verdict

MAX_FEEDBACK_WORDS = 30
MAX_HINT_WORDS = 18
MAX_SUMMARY_WORDS = 90
MAX_ITEM_WORDS = 20

# Claims that the answer was right, when the deterministic outcome says otherwise.
_CLAIMS_CORRECT = (
    r"\b(correct|right answer|that'?s right|you got it|perfect|exactly right|spot on)\b"
)
_CLAIMS_WRONG = r"\b(wrong|incorrect|mistake|not quite|not right)\b"
# Clinician summaries may name the condition but never diagnose, predict or prescribe.
_SUMMARY_UNSAFE = {
    "medical_claim": r"\b(diagnos\w*|prognos\w*|medicat\w*|prescri\w*|cure\w*|heal\w*|"
    r"brain|damage|treatment plan|will recover|recovery will)\b",
    "link_or_contact": _UNSAFE_PATTERNS["link_or_contact"],
}


def _parse[M: BaseModel](raw: str, model: type[M]) -> tuple[M | None, Verdict | None]:
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None, Verdict(False, "schema", ["invalid_json"])
    if not isinstance(data, dict):
        return None, Verdict(False, "schema", ["not_an_object"])
    try:
        return model.model_validate(data), None
    except ValidationError as e:
        codes = sorted({f"{err['type']}:{'.'.join(map(str, err['loc']))}" for err in e.errors()})
        return None, Verdict(False, "schema", codes)


def check_feedback(raw: str, outcome: str) -> tuple[Verdict, FeedbackOutput | None]:
    out, failed = _parse(raw, FeedbackOutput)
    if failed or out is None:
        return failed or Verdict(False, "schema", ["invalid"]), None
    reasons: list[str] = []
    texts = [("feedback", out.feedback, MAX_FEEDBACK_WORDS)]
    if out.optional_hint:
        texts.append(("optional_hint", out.optional_hint, MAX_HINT_WORDS))
    for name, text, max_words in texts:
        if len(text.split()) > max_words:
            reasons.append(f"too_long:{name}")
        for code, pattern in _UNSAFE_PATTERNS.items():
            if re.search(pattern, text, re.IGNORECASE):
                reasons.append(f"{code}:{name}")
        if outcome != "correct" and re.search(_CLAIMS_CORRECT, text, re.IGNORECASE):
            reasons.append(f"contradicts_score:{name}")
        if outcome == "correct" and re.search(_CLAIMS_WRONG, text, re.IGNORECASE):
            reasons.append(f"contradicts_score:{name}")
    return Verdict(not reasons, None if not reasons else "safety", reasons), out


def allowed_numbers(inp: dict[str, Any]) -> set[str]:
    """Every number the summary input contains; the model may only repeat these."""
    found: set[str] = set()

    def walk(v: Any) -> None:
        if isinstance(v, bool):
            return
        if isinstance(v, int | float):
            found.add(str(round(v)) if float(v).is_integer() else str(v))
        elif isinstance(v, str):
            found.update(re.findall(r"\d+(?:\.\d+)?", v))
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)

    walk(inp)
    return found


def check_summary(raw: str, inp: dict[str, Any]) -> tuple[Verdict, SummaryOutput | None]:
    out, failed = _parse(raw, SummaryOutput)
    if failed or out is None:
        return failed or Verdict(False, "schema", ["invalid"]), None
    reasons: list[str] = []
    numbers = allowed_numbers(inp)
    texts = [("summary", out.summary, MAX_SUMMARY_WORDS)]
    texts += [(f"strengths.{i}", t, MAX_ITEM_WORDS) for i, t in enumerate(out.strengths)]
    texts += [(f"focus_areas.{i}", t, MAX_ITEM_WORDS) for i, t in enumerate(out.focus_areas)]
    for name, text, max_words in texts:
        if len(text.split()) > max_words:
            reasons.append(f"too_long:{name}")
        for code, pattern in _SUMMARY_UNSAFE.items():
            if re.search(pattern, text, re.IGNORECASE):
                reasons.append(f"{code}:{name}")
        invented = [n for n in re.findall(r"\d+(?:\.\d+)?", text) if n not in numbers]
        if invented:
            reasons.append(f"invented_number:{name}")
    return Verdict(not reasons, None if not reasons else "safety", reasons), out
