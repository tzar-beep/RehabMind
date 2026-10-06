"""Deterministic scoring for single-word naming responses.

Rule-based by design: cheap, testable, and explainable to clinicians. Outcomes describe
the response, not the patient; they are personalization signals, not clinical scores.
"""

import re
from dataclasses import dataclass, field
from typing import Literal

Outcome = Literal["correct", "near_miss", "incorrect", "skipped"]

NEAR_MISS_THRESHOLD = 0.75
_ARTICLES = {"a", "an", "the", "some"}
_FILLERS = {"it", "is", "its", "it's", "thats", "that's", "this", "that", "i", "think"}
_NEGATIONS = {"not", "no", "isn't", "isnt"}
_SKIP_PHRASES = {"", "skip", "pass", "idk", "i dont know", "i don't know", "dont know", "not sure"}


@dataclass(frozen=True)
class ScoreResult:
    outcome: Outcome
    score: float
    match_type: str  # exact | accepted_variant | plural | in_phrase | similar | none | skipped
    matched: str | None = None
    similarity: float | None = None
    details: dict[str, object] = field(default_factory=dict)


def normalize(text: str) -> str:
    text = text.lower().replace("’", "'")
    text = re.sub(r"[^a-z' ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _strip_articles(text: str) -> str:
    words = text.split()
    while words and words[0] in _ARTICLES:
        words = words[1:]
    return " ".join(words)


def similarity(a: str, b: str) -> float:
    """1 - normalized Levenshtein distance."""
    if a == b:
        return 1.0
    if not a or not b:
        return 0.0
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return 1 - prev[-1] / max(len(a), len(b))


def score_naming(response: str | None, target: str, accepted: list[str]) -> ScoreResult:
    raw = normalize(response or "")
    if raw in _SKIP_PHRASES:
        return ScoreResult("skipped", 0.0, "skipped")

    answer = _strip_articles(raw)
    accepted_norm = [normalize(a) for a in accepted]
    target_norm = normalize(target)

    if answer == target_norm:
        return ScoreResult("correct", 1.0, "exact", target_norm)
    if answer in accepted_norm:
        return ScoreResult("correct", 1.0, "accepted_variant", answer)
    if answer.endswith("s") and answer[:-1] in accepted_norm:
        return ScoreResult("correct", 1.0, "plural", answer[:-1])

    # Short carrier phrases ("it's a cup"): accept if a target appears as a whole phrase.
    words = answer.split()
    content = " ".join(w for w in words if w not in _FILLERS | _ARTICLES)
    if not (_NEGATIONS & set(words)) and len(content.split()) <= 4:
        for a in accepted_norm:
            if f" {a} " in f" {content} ":
                return ScoreResult("correct", 1.0, "in_phrase", a)

    best, best_sim = max(
        ((a, similarity(content or answer, a)) for a in accepted_norm), key=lambda x: x[1]
    )
    if best_sim >= NEAR_MISS_THRESHOLD and len(best) >= 3:
        return ScoreResult("near_miss", round(best_sim, 3), "similar", best, round(best_sim, 3))
    return ScoreResult("incorrect", 0.0, "none", None, round(best_sim, 3))


# ---------- picture description: concept coverage ----------

DESCRIPTION_PARTIAL = 0.5  # at least half the key concepts → "close"


def _contains(text: str, term: str) -> bool:
    return f" {normalize(term)} " in f" {text} "


def score_description(response: str | None, concepts: list[dict]) -> ScoreResult:
    """Count how many key concepts (each with accepted terms) the answer mentions.

    Required concepts decide the outcome; optional ones (setting details such as "grass")
    are credited when mentioned but never required.
    """
    text = normalize(response or "")
    if text in _SKIP_PHRASES:
        return ScoreResult(
            "skipped", 0.0, "skipped", details={"concepts_matched": [], "concepts_missing": []}
        )
    matched = [c["name"] for c in concepts if any(_contains(text, t) for t in c["terms"])]
    required = [c["name"] for c in concepts if not c.get("optional")]
    missing = [name for name in required if name not in matched]
    ratio = (len(required) - len(missing)) / len(required) if required else 0.0
    outcome: Outcome = (
        "correct" if not missing else "near_miss" if ratio >= DESCRIPTION_PARTIAL else "incorrect"
    )
    return ScoreResult(
        outcome,
        round(ratio, 3),
        "concepts",
        details={"concepts_matched": matched, "concepts_missing": missing},
    )


# ---------- sentence construction: normalized exact match ----------


def _sentence_key(text: str) -> str:
    return " ".join(normalize(text).split())


def score_sentence(response: str | None, target: str, accepted: list[str]) -> ScoreResult:
    """Correct if the sentence matches an accepted variant (case/punctuation/spacing ignored);
    close if it uses exactly the right words in a different order."""
    answer = _sentence_key(response or "")
    if answer in _SKIP_PHRASES:
        return ScoreResult("skipped", 0.0, "skipped")
    variants = {_sentence_key(v) for v in [target, *accepted]}
    if answer in variants:
        return ScoreResult("correct", 1.0, "exact", answer)
    if sorted(answer.split()) == sorted(_sentence_key(target).split()):
        return ScoreResult("near_miss", 0.5, "word_order")
    return ScoreResult("incorrect", 0.0, "none")


def score_exercise(exercise_type: str, response: str | None, expected: dict) -> ScoreResult:
    if exercise_type == "picture_description":
        return score_description(response, expected["concepts"])
    if exercise_type == "sentence_construction":
        return score_sentence(response, expected["target"], expected.get("accepted_answers", []))
    return score_naming(response, expected["target"], expected["accepted_answers"])
