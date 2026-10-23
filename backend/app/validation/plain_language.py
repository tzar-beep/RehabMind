"""Aphasia-friendly language checks for patient-facing AI text.

Accessible-information guidance for people with aphasia (Aphasia Institute; Stroke
Association; Herbert et al. 2012) asks for short sentences, everyday words and an adult,
respectful tone. The guidance gives no validated numbers, so the thresholds here are design
choices to be confirmed by the clinician panel (docs/validation/protocols/).
"""

import re
from functools import cache

from app.analysis.scoring import normalize

# Zipf 3 ~ once per million words. Words rarer than this are unlikely to be easy to read.
MIN_EVERYDAY_ZIPF = 3.0
MAX_SENTENCE_WORDS = 12
# Childish or patronising address, and over-the-top praise (respectful adult tone).
_PATRONISING = (
    r"\b(sweetie|sweetheart|honey|dear|buddy|kiddo|little one|good (boy|girl)|"
    r"clever (boy|girl)|aww+|yay+|super ?duper|big boy|big girl|silly)\b"
)


@cache
def _zipf(word: str) -> float:
    from wordfreq import zipf_frequency

    return zipf_frequency(word, "en")


def rare_words(text: str, allowed: set[str] = frozenset()) -> list[str]:
    """Words in `text` rarer than everyday English, except names the task itself uses."""
    words = re.findall(r"[a-z]+(?:'[a-z]+)?", normalize(text))
    return [w for w in words if w not in allowed and _zipf(w) < MIN_EVERYDAY_ZIPF]


def long_sentences(text: str) -> bool:
    return any(len(s.split()) > MAX_SENTENCE_WORDS for s in re.split(r"[.!?]+", text))


def check(text: str, name: str, allowed: set[str] = frozenset()) -> list[str]:
    """Reason codes for one patient-facing text, in the validators' `code:field` format."""
    reasons = []
    if rare_words(text, allowed):
        reasons.append(f"rare_word:{name}")
    if long_sentences(text):
        reasons.append(f"long_sentence:{name}")
    if re.search(_PATRONISING, text, re.IGNORECASE):
        reasons.append(f"patronising:{name}")
    return reasons
