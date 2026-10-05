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

`backend/app/exercises/stimuli_catalog.json` is the reviewed source of truth: target word,
accepted answers, category, difficulty (1–5). Images are Lucide line drawings (ISC licence),
copied to `frontend/public/stimuli/` by `npm run copy-stimuli`; DB sync via
`uv run python -m app.scripts.sync_stimuli`. AI never creates images; from Phase 4 it may
only choose from and phrase around this library. The library can be replaced (e.g. clinically
validated photographs) without code changes.

## Scoring (rules-v1)

Normalized text → `correct` (exact / accepted variant / plural / short carrier phrase
such as "it's a cup", unless negated) → `near_miss` (edit similarity ≥ 0.75) → `incorrect`;
empty or "I don't know" → `skipped`. These are personalization signals, **not** clinical
assessments.
