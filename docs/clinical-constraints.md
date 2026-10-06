# Clinical constraints and the practice loop

## Constraint sets

A clinician (assigned to the patient) defines a **constraint set**:

| Field | Meaning |
|---|---|
| `allowed_exercise_types` | Types that may be issued. Unimplemented types are accepted but never issued. |
| `allowed_response_modes` | `text`, `speech` (speech from Phase 3) |
| `allowed_categories` | Picture categories; `null` = all |
| `min_difficulty` / `max_difficulty` | Hard range, 1–5 |
| `max_exercises_per_session` | 1–50 |
| `advance_after_correct` / `step_back_after_incorrect` | Progression rule thresholds |

Sets are **immutable versions** (`POST /patients/{id}/constraints` appends version N+1).
The newest version applies to the **very next exercise**, including mid-session.

## Enforcement layers (MAX_DIFFICULTY = 3 ⇒ never difficulty 4)

1. **Progression** (`performance/progression.py`) proposes a working level, clamped to the range.
2. **Generator** (`exercises/generator.py`) only selects stimuli inside the range/categories.
3. **ExerciseIssuer** (`exercises/issuer.py`) — the only code that creates exercises — validates
   every proposal and returns reason codes on rejection. Rejections are audited
   (`exercise.rejected`) and replaced by a deterministic **fallback** (minimum difficulty).
   If no safe exercise exists, the patient sees a calm message; nothing unsafe is issued.
4. **Database trigger** `enforce_exercise_constraints` rejects any exercise row that is out of
   range, uses a disallowed type/mode, belongs to another patient's set, or references a
   non-latest version. The runtime DB role cannot disable it or edit constraint sets.

Covered by `tests/test_practice.py` (all-correct patients at max 1–4, mid-session lowering,
categories, trigger bypass attempts) and a Hypothesis property test on progression.

## Picture library

`backend/app/exercises/stimuli_catalog.json` is the reviewed source of truth, stored locally
(no runtime downloads):

| Kind | Count | Used for | Licence |
|---|---|---|---|
| Real-world photos (`frontend/public/stimuli/photos/`) | 61 (43 objects, 18 scenes) | picture naming; picture description and sentence construction (scenes) | CC0 / public domain / CC BY / CC BY-SA, from Wikimedia Commons; see [photo-credits.md](photo-credits.md) |
| Lucide line drawings | 41 | picture naming (fallback) | ISC |

Each entry has category, difficulty (1–5), the exercise types it supports, the canonical
answer and accepted variants, and, for scenes, description concepts and sentence words.
Photos are preferred whenever one exists inside the clinician's limits; drawings remain the
fallback. The AI only picks a catalogue entry by slug: it never supplies image paths, and an
entry without content for the exercise type is rejected.

## Exercise types (implemented)

The issuer rotates through the clinician-allowed types (naming → sentence → description),
each with its own working difficulty.

| Type | Patient does | Scoring (deterministic, no AI) |
|---|---|---|
| Picture naming | says/types the word | exact / accepted variant / plural / short phrase → correct; edit similarity ≥ 0.75 → close |
| Sentence construction | taps scrambled words into order (or says the sentence) | normalized match against accepted variants → correct; right words, wrong order → close |
| Picture description | says/types a description | key concepts (each with accepted terms) mentioned: all required → correct; ≥ half → close. Setting details are optional extras |

Outcomes are personalization signals, **not** clinical assessments. Word repetition, word
recognition, sentence completion and category naming remain not implemented.
