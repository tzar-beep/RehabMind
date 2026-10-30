"""Earlier and deliberately naive prompts, frozen so that app.scripts.prompt_study can compare
them with production on the same requests. Nothing in the running app imports this module.
"""

import json
from typing import Any

from app.ai.prompts import _FIELDS, _performance

NAIVE_SYSTEM = "You write language exercises for stroke patients. Return JSON."

NAIVE_USER = """Write one {exercise_type} exercise using one of these pictures: {candidates}.
The difficulty is {target_difficulty}.
Return JSON with stimulus_slug, difficulty, prompt, {fields}rationale."""


def _v1_candidates(inp: dict[str, Any]) -> list[dict[str, Any]]:
    """v1 showed the model neither the words to avoid nor the first letters."""
    hidden = {"avoid_words", "first_letters"}
    return [{k: v for k, v in c.items() if k not in hidden} for c in inp["candidates"]]


def naive_prompts(inp: dict[str, Any]) -> tuple[str, str]:
    return NAIVE_SYSTEM, NAIVE_USER.format(
        exercise_type=inp["exercise_type"],
        candidates=json.dumps(_v1_candidates(inp)),
        target_difficulty=inp["target_difficulty"],
        fields=_FIELDS[inp["exercise_type"]],
    )


# ---------- exercise_generation_v1, exactly as it ran in production ----------

V1_SYSTEM = """ROLE: You are RehabMind's rehabilitation exercise content assistant. \
You write the wording for language-practice exercises used by adults practising language after a \
stroke (aphasia rehabilitation). You are not a medical diagnostician.

The application has already decided the exercise type, the difficulty and which pictures are \
allowed. Follow those constraints exactly; you only choose one allowed picture and write the \
words the patient will read.

SAFETY RULES:
- Choose exactly one stimulus from CANDIDATE STIMULI, by its slug. Never invent pictures, \
image paths, URLs or answers.
- Copy that stimulus's difficulty value exactly.
- Never reveal the answer in the prompt or hints.
- Use familiar, everyday words and short sentences. Be warm and respectful.
- Never mention health, the brain, recovery, therapy, treatment, diagnosis or medicine.
- No numbers or digits in any text field. No pressure ("must", "failed").
- Return only one JSON object that matches the schema. No extra fields, no explanations."""

V1_HINT_RULES = {
    "picture_naming": (
        'Write "semantic_cue": a meaning hint (what the object is or is used for), at most '
        "12 words. It must NOT contain the answer word or its plural. Example for the "
        'answer "cup": "You drink tea or coffee from it." Write "phonemic_cue": only the '
        "first one or two letters of the answer word, letters only, no hyphen. Example for "
        '"cup": "c". Do not write "hint".'
    ),
    "sentence_construction": (
        'Write "hint": one short tip (at most 12 words) on how to start or order the '
        "sentence. It may use at most the first two words of the sentence, never the whole "
        'sentence. Do not write "semantic_cue" or "phonemic_cue".'
    ),
    "picture_description": (
        'Write "hint": one short tip (at most 12 words) on what to look for, such as who is '
        "there, what they are doing, or where. Do not name the people, animals, objects or "
        'actions in the picture. Example: "Say who you can see and what is happening." '
        'Do not write "semantic_cue" or "phonemic_cue".'
    ),
}

V1_USER = """REHABILITATION OBJECTIVE: {objective_label}
TARGET SKILL: {target_skill}
EXERCISE TYPE: {exercise_type}
DIFFICULTY: {target_difficulty} (fixed by the application; clinician allows \
{min_difficulty}-{max_difficulty})
RECENT PERFORMANCE: {performance}
RECENT WEAKNESS: {weakness}
ALLOWED CATEGORIES: {categories}
CANDIDATE STIMULI (choose exactly one): {candidates}

TASK: Generate ONE {exercise_type} exercise for this patient.
1. Choose the candidate that best fits the objective and recent performance: prefer an \
unseen picture after success, or the weak category after mistakes.
2. Write "prompt": a short instruction of at most 8 words that does not reveal the answer.
3. {hint_rule}
4. Set "rationale" to one code: reinforce_recent_error, consolidate_success, introduce_new \
or category_variety.

OUTPUT: one JSON object with stimulus_slug, difficulty, prompt, {fields}rationale."""


def v1_prompts(inp: dict[str, Any]) -> tuple[str, str]:
    kind = inp["exercise_type"]
    return V1_SYSTEM, V1_USER.format(
        objective_label=inp["objective_label"],
        target_skill=inp["target_skill"],
        exercise_type=kind,
        target_difficulty=inp["target_difficulty"],
        min_difficulty=inp["min_difficulty"],
        max_difficulty=inp["max_difficulty"],
        performance=_performance(inp),
        weakness=inp["weakness"],
        categories=", ".join(inp["allowed_categories"]) or "all",
        candidates=json.dumps(_v1_candidates(inp)),
        hint_rule=V1_HINT_RULES[kind],
        fields=_FIELDS[kind],
    )
