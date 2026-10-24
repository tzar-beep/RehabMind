"""Psycholinguistic difficulty estimate for picture-naming targets.

Naming difficulty in aphasia is predicted by age of acquisition, imageability, length and
name agreement more than by raw frequency (Nickels & Howard 1995). Only frequency and
length are available offline today (wordfreq, bundled): this estimate uses those two, so it
is a first check on the hand-assigned levels, not a replacement for them. Adding Kuperman
age-of-acquisition and Glasgow imageability norms is listed in docs/validation/difficulty.md.
"""

import re
from dataclasses import dataclass
from statistics import mean, pstdev

from wordfreq import zipf_frequency

# Weight of each standardised predictor in the combined score (higher = harder).
W_FREQUENCY = 1.0
W_SYLLABLES = 0.7
W_MULTIWORD = 0.3
# Name agreement (BOSS norms): pictures that people name inconsistently are harder to name
# and harder to score. Weighted like frequency (Nickels & Howard 1995 rank it above it).
W_AGREEMENT = 1.0


def syllables(word: str) -> int:
    """Vowel-group count with a silent-e correction; within one syllable for common nouns."""
    total = 0
    for w in word.lower().split():
        groups = re.findall(r"[aeiouy]+", w)
        n = len(groups)
        if w.endswith("e") and not w.endswith(("le", "ee")) and n > 1:
            n -= 1
        total += max(1, n)
    return total


@dataclass(frozen=True)
class WordNorms:
    target: str
    zipf: float
    syllables: int
    words: int


def norms(target: str) -> WordNorms:
    words = target.lower().split()
    # Compounds: the phrase if the corpus knows it, otherwise its rarest word.
    z = zipf_frequency(target, "en") or min(zipf_frequency(w, "en") for w in words)
    return WordNorms(target, z, syllables(target), len(words))


def _standardise(values: list[float]) -> list[float]:
    sd = pstdev(values) or 1.0
    m = mean(values)
    return [(v - m) / sd for v in values]


def estimate_levels(
    targets: list[str], levels: int = 5, agreement: dict[str, float] | None = None
) -> dict[str, tuple[WordNorms, int]]:
    """Rank targets by the combined score and cut the ranking into equal-sized levels.

    `agreement`: name agreement (0-1) per target; when given, lower agreement ranks harder.
    """
    unique = sorted(set(targets))
    n = [norms(t) for t in unique]
    freq = _standardise([-x.zipf for x in n])
    syl = _standardise([float(x.syllables) for x in n])
    multi = [1.0 if x.words > 1 else 0.0 for x in n]
    agree = _standardise([-agreement[t] for t in unique]) if agreement else [0.0] * len(unique)
    scores = [
        W_FREQUENCY * f + W_SYLLABLES * s + W_MULTIWORD * m + W_AGREEMENT * a
        for f, s, m, a in zip(freq, syl, multi, agree, strict=True)
    ]
    order = sorted(range(len(unique)), key=lambda i: scores[i])
    out: dict[str, tuple[WordNorms, int]] = {}
    for rank, i in enumerate(order):
        out[unique[i]] = (n[i], 1 + rank * levels // len(unique))
    return out
