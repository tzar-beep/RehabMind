"""Clinical error type for picture-naming responses, adapted from the Philadelphia Naming Test.

The PNT (Roach et al. 1996) classifies a naming attempt by asking, in order: is it a real
word? does it sound like the target? is it related in meaning? ParAlg (Casilio, Fergadiotis
et al. 2023) showed this decision tree can be automated from transcriptions. This is a
simpler, text-only version of the same tree:

    no_response        skipped / "I don't know"
    correct            scored correct by app.analysis.scoring
    description        three or more content words without the target (circumlocution)
    semantic           real word related in meaning      (dog -> "cat", "bone", "animal")
    formal             real word that sounds similar     (dog -> "log")
    mixed              real word, similar in both ways   (cat -> "rat")
    unrelated          real word, neither                (dog -> "spoon")
    nonword_related    not a word, sounds like target    (dog -> "dob"; typed: misspelling)
    nonword_unrelated  not a word, does not              (dog -> "flimp")

Limits (also in docs/validation/scoring.md): sound similarity is approximated from spelling,
"real word" comes from corpus frequency (wordfreq), and meaning relations come from a small
curated lexicon. The error type is descriptive information for clinicians. It never changes
the outcome, the progression, or anything the patient sees.
"""

import json
import re
from functools import cache
from pathlib import Path
from typing import Literal

from app.analysis.scoring import _ARTICLES, _FILLERS, _NEGATIONS, normalize, similarity

ErrorType = Literal[
    "correct",
    "no_response",
    "description",
    "semantic",
    "formal",
    "mixed",
    "unrelated",
    "nonword_related",
    "nonword_unrelated",
]
ERROR_TYPES: tuple[ErrorType, ...] = ErrorType.__args__  # type: ignore[attr-defined]

LEXICON_PATH = Path(__file__).with_name("semantic_lexicon.json")
# wordfreq Zipf scale: 1 = once per 100 million words. Below this a string is treated as a
# non-word. Low on purpose: rare real words ("tog", "awl") should still count as words.
MIN_WORD_ZIPF = 2.0
FORMAL_SIMILARITY = 0.5
DESCRIPTION_MIN_WORDS = 3
# Hesitations and "can't recall" phrases: the PNT scores these as no response.
_HESITATIONS = {"um", "uh", "uhh", "umm", "er", "erm", "hmm", "mm", "ah", "sorry", "please"}
_NO_RESPONSE = re.compile(
    r"\b(don'?t|do not) know\b|\bno idea\b|\bdunno\b|\bcan'?t\b|\bcannot\b"
    r"|\bforg[eo]t\b|^(no|pass|skip|idk)$"
)

# Spelling -> rough sound, applied in order. Enough to make "phone"/"fone", "knife"/"nife"
# and "cat"/"kat" sound alike; not a pronunciation dictionary.
_SOUND_RULES = [
    (r"^kn", "n"),
    (r"^wr", "r"),
    (r"^gn", "n"),
    (r"^wh", "w"),
    (r"tch", "ch"),
    (r"dge", "j"),
    (r"ph", "f"),
    (r"ck", "k"),
    (r"qu", "kw"),
    (r"x", "ks"),
    (r"c(?=[eiy])", "s"),
    (r"c", "k"),
    (r"gh", ""),
    (r"(ee|ea|ie)", "i"),
    (r"(oo|ou)", "u"),
    (r"e?y$", "i"),
    (r"(?<=[a-z]{2}[^aeiou])e$", ""),  # silent final e: "plate" -> "plat"
    (r"(.)\1", r"\1"),
]


def sounds(word: str) -> str:
    s = re.sub(r"[^a-z]", "", word.lower())
    for pattern, repl in _SOUND_RULES:
        s = re.sub(pattern, repl, s)
    return s


def sounds_similar(a: str, b: str) -> bool:
    """PNT formal-similarity criterion, approximated: same first or last sound, or at least
    half the sound string in common."""
    sa, sb = sounds(a), sounds(b)
    if not sa or not sb or sa == sb:
        return bool(sa) and sa == sb
    return sa[0] == sb[0] or sa[-1] == sb[-1] or similarity(sa, sb) >= FORMAL_SIMILARITY


@cache
def _lexicon() -> dict:
    return json.loads(LEXICON_PATH.read_text(encoding="utf-8"))


@cache
def _known_words() -> frozenset[str]:
    lex = _lexicon()
    words = {w for ws in lex["fields"].values() for w in ws}
    words |= {w for ws in lex["superordinates"].values() for w in ws}
    words |= {w for ws in lex["associates"].values() for w in ws}
    return frozenset(words)


def related_words(target: str, accepted: list[str]) -> set[str]:
    """Words related in meaning: same semantic field, its superordinates, and associates."""
    lex = _lexicon()
    names = {normalize(target), *(normalize(a) for a in accepted)}
    related: set[str] = set()
    for field, members in lex["fields"].items():
        if names & set(members):
            related |= set(members) | set(lex["superordinates"].get(field, []))
    for name in names:
        related |= set(lex["associates"].get(name, []))
    return related - names


def is_word(text: str) -> bool:
    if text in _known_words():
        return True
    from wordfreq import zipf_frequency

    return all(zipf_frequency(w, "en") >= MIN_WORD_ZIPF for w in text.split())


def content_words(response: str) -> list[str]:
    return [w for w in normalize(response).split() if w not in _ARTICLES | _FILLERS]


def classify_naming(
    response: str | None, target: str, accepted: list[str], outcome: str
) -> ErrorType:
    if outcome == "skipped":
        return "no_response"
    if outcome == "correct":
        return "correct"
    text = normalize(response or "")
    words = [w for w in content_words(text) if w not in _HESITATIONS]
    if not words or _NO_RESPONSE.search(" ".join(words)) or _NO_RESPONSE.search(text):
        return "no_response"
    if len(words) >= DESCRIPTION_MIN_WORDS or _NEGATIONS & set(words):
        return "description"

    related = related_words(target, accepted)
    phrase = " ".join(words)
    # Two words: the phrase may be a compound ("light bulb"); otherwise judge the head noun.
    candidate = phrase if phrase in related or len(words) == 1 else words[-1]
    semantic = candidate in related
    # Sound similarity is judged against the target name only, as in the PNT.
    formal = sounds_similar(candidate, normalize(target).split()[-1]) or sounds_similar(
        candidate, normalize(target)
    )

    if not (semantic or is_word(candidate)):
        return "nonword_related" if formal else "nonword_unrelated"
    if semantic and formal:
        return "mixed"
    if semantic:
        return "semantic"
    if formal:
        return "formal"
    return "unrelated"
