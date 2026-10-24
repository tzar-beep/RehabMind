"""Phase 1 dry run: language-model raters fill in the clinician panel's packets.

    uv run python -m app.scripts.simulate_panel        # needs Ollama with the configured model
    uv run python -m app.scripts.analyse_panel analyse --panel simulated/panel \
        --report phase1-simulated.md

SYNTHETIC RATINGS. No clinician took part. Three rater personas (prompts) rate the 48
content items blind to their source, and two label the 200 answers, with exactly the
instructions and scales the human panel gets (protocols/phase1-slp-panel.md). The ratings are
written where returned panel files go, under docs/validation/simulated/panel/, and analysed
by the same script.

What this shows: the packets, instructions and analysis work end to end, and how a small
local model judges the items. What it cannot show: clinical content validity. A 3-billion-
parameter model is not a speech and language therapist; studies of LLM-as-judge find
agreement with experts varies widely by task. Real panel ratings replace these files.
"""

import asyncio
import csv
import json
import sys
from pathlib import Path

import httpx

from app.analysis.errors import ERROR_TYPES
from app.core.config import get_settings

ROOT = Path(__file__).parents[3] / "docs" / "validation"
PACKETS = ROOT / "review-packets"
OUT = ROOT / "simulated" / "panel"

CONTENT_RATERS = {
    "sim-rater-a": "an experienced speech and language therapist who has treated aphasia "
    "after stroke for fifteen years. You are strict about wording that could confuse.",
    "sim-rater-b": "a speech and language therapist two years after qualifying, working on a "
    "stroke ward. You judge items by whether your patients could use them today.",
    "sim-rater-c": "a speech and language therapy lecturer who researches naming treatment "
    "for aphasia. You check items against what the research recommends.",
}
SCORING_RATERS = {k: CONTENT_RATERS[k] for k in ("sim-rater-a", "sim-rater-b")}

CONTENT_TASK = """You are rating one picture-naming exercise for adults with aphasia after \
stroke. The patient sees a photo of the picture and the question, and can ask for the \
meaning cue, then the sound cue.

PICTURE: {picture}
QUESTION: {question}
MEANING CUE: {meaning_cue}
SOUND CUE: {sound_cue}

Rate each from 1 to 4:
- relevance: is this a relevant exercise for practising word finding? (1 not relevant, \
4 highly relevant)
- clarity: are the question and cues clear and easy to read for a person with aphasia?
- tone: is the tone respectful and suitable for an adult?
- difficulty_fit: do the cues help without giving the word away?
Add a short comment (at most 15 words).
Return one JSON object with relevance, clarity, tone, difficulty_fit and comment."""

SCORING_TASK = """You are scoring one spoken or typed answer in a picture-naming test, as \
in the Philadelphia Naming Test.

PICTURE (the expected name): {picture}
ANSWER: "{response}"

Decide "correct": "yes" if the answer names the picture (an accepted synonym, a plural or \
the name inside a short phrase counts), otherwise "no".
Decide "error_type", one of:
- correct: the picture was named
- no_response: no attempt, "I don't know", or only hesitation sounds
- description: describes the object instead of naming it (three or more words)
- semantic: a real word related in meaning (cat for dog)
- formal: a real word that sounds like the target but is unrelated in meaning (log for dog)
- mixed: a real word related in both meaning and sound (rat for cat)
- unrelated: a real word related in neither
- nonword_related: not a real word, sharing sounds with the target (dag for dog)
- nonword_unrelated: not a real word, not like the target
Return one JSON object with correct and error_type."""

CONTENT_SCHEMA = {
    "type": "object",
    "properties": {
        **{
            d: {"type": "integer", "minimum": 1, "maximum": 4}
            for d in ("relevance", "clarity", "tone", "difficulty_fit")
        },
        "comment": {"type": "string"},
    },
    "required": ["relevance", "clarity", "tone", "difficulty_fit", "comment"],
}
SCORING_SCHEMA = {
    "type": "object",
    "properties": {
        "correct": {"type": "string", "enum": ["yes", "no"]},
        "error_type": {"type": "string", "enum": list(ERROR_TYPES)},
    },
    "required": ["correct", "error_type"],
}


async def ask(client: httpx.AsyncClient, model: str, persona: str, task: str, schema) -> dict:
    r = await client.post(
        "/api/chat",
        json={
            "model": model,
            "stream": False,
            "format": schema,
            "options": {"temperature": 0.7},
            "messages": [
                {"role": "system", "content": f"You are {persona} Answer only with JSON."},
                {"role": "user", "content": task},
            ],
        },
    )
    r.raise_for_status()
    return json.loads(r.json()["message"]["content"])


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


async def main_async() -> None:
    settings = get_settings()
    items = _read(PACKETS / "phase1-items.csv")
    answers = _read(PACKETS / "phase1-scoring.csv")
    async with httpx.AsyncClient(base_url=settings.ollama_base_url, timeout=120) as client:
        for name, persona in CONTENT_RATERS.items():
            rows = []
            for it in items:
                out = await ask(
                    client,
                    settings.ollama_model,
                    persona,
                    CONTENT_TASK.format(**it),
                    CONTENT_SCHEMA,
                )
                rows.append(
                    {"item_id": it["item_id"], **{k: out[k] for k in CONTENT_SCHEMA["required"]}}
                )
            _write(OUT / "content" / f"{name}.csv", rows)
            print(f"content: {name} rated {len(rows)} items", flush=True)
        for name, persona in SCORING_RATERS.items():
            rows = []
            for a in answers:
                out = await ask(
                    client,
                    settings.ollama_model,
                    persona,
                    SCORING_TASK.format(picture=a["picture"], response=a["response"]),
                    SCORING_SCHEMA,
                )
                rows.append({"item_id": a["item_id"], **out})
            _write(OUT / "scoring" / f"{name}.csv", rows)
            print(f"scoring: {name} labelled {len(rows)} answers", flush=True)


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
