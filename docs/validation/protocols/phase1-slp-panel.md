# Phase 1 protocol: speech and language therapist panel

**Aim.** Get clinician judgements on (A) whether RehabMind's generated exercise text is
appropriate for aphasia practice, and (B) whether its scoring agrees with how clinicians
score naming answers.

**Ethics.** Clinicians rate materials; no patient data is involved. Submit to the
institutional ethics committee (IEC) for exempt or expedited review
([ethics-and-consent.md](ethics-and-consent.md)). Raters give written consent and may
withdraw at any time.

## Participants

- 3-6 speech and language therapists (SLPs) with at least 2 years of adult neurological
  caseload. Six gives the most stable content validity thresholds (Polit, Beck & Owen 2007).
- At least 2 of them also do Part B, independently.
- Recruit through the faculty supervisor's clinical contacts or a hospital SLP department.
  Offer a certificate of contribution; there is no payment requirement.

## Materials (in `docs/validation/review-packets/`)

| File | Give to raters? | Contents |
|---|---|---|
| `phase1-items.csv` | Yes | 48 picture-naming items: question, meaning cue, sound cue. Half AI-written, half rule-based, shuffled |
| `phase1-key.csv` | **No** | Which items are AI-written. Opened only for analysis |
| `phase1-scoring.csv` | Yes | 200 naming answers to label |
| `phase1-scoring-key.csv` | **No** | The app's decisions. Opened only for analysis |

Pictures: the `image` column names the file in `frontend/public/stimuli/` (photos) or the
catalogue icon. Put the pictures next to the items when printing or sharing the sheet.

## Part A: content ratings (about 45 minutes)

1. **Calibration (10 minutes, together or by video call).** Rate 4 practice items not in the
   packet, compare ratings, and agree what each scale point means. The precedent study of
   GPT-4 therapy materials found poor agreement across 12 SLPs (ICC 0.45), which a short
   calibration helps avoid.
2. **Independent rating.** Each rater copies `phase1-items.csv`, adds four columns, and
   rates every item from 1 to 4:

| Column | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| `relevance` | Not relevant for naming practice in aphasia | Somewhat relevant, needs major revision | Relevant, needs minor revision | Highly relevant as it is |
| `clarity` | Confusing | Hard to follow | Mostly clear | Clear and easy for a person with aphasia |
| `tone` | Inappropriate (childish, pressuring, medical) | Some problems | Mostly respectful | Adult and respectful |
| `difficulty_fit` | Cues give away the answer or do not help | Cues weak or misleading | Cues reasonable | Cues follow a good cueing hierarchy |

   Plus an optional `comment`. Rate the cues on their own merits: rule-based questions all
   say "What is this?", so the question wording can reveal the source.
3. Save as `docs/validation/panel/content/<rater-code>.csv` (for example `slp1.csv`). Use
   codes, not names.

## Part B: scoring labels (about 2 hours, at least 2 raters)

Fill in `phase1-scoring.csv` independently:

- `correct`: `yes` if you would accept the answer as a correct naming response, else `no`.
- `error_type`: one of `correct`, `no_response`, `description`, `semantic`, `formal`,
  `mixed`, `unrelated`, `nonword_related`, `nonword_unrelated` (definitions in
  [scoring.md](../scoring.md); they follow the PNT categories). Score the answer as written;
  typed misspellings count as `nonword_related` unless you would accept them.

Save as `docs/validation/panel/scoring/<rater-code>.csv`.

## Part C (optional): clinician console walkthrough (30 minutes)

Each SLP uses the clinician pages with a seeded demo patient: read the overview, open a
session, change the practice limits (including the progression mode), and read the AI audit
log. Afterwards: System Usability Scale (SUS), plus three questions: "Would you trust the
level the app chooses?", "What would you change before using it with a patient?", "Which
information was missing?".

## Analysis

```bash
cd backend
uv run python -m app.scripts.analyse_panel analyse    # writes docs/validation/results/panel.md
```

| Measure | Threshold | Source |
|---|---|---|
| Item content validity index (I-CVI) | ≥ 0.78 | Lynn 1986; Polit, Beck & Owen 2007 |
| Scale average (S-CVI/Ave) | ≥ 0.90 | Polit & Beck 2006 |
| Rater-rater κ (correct/incorrect) | ≥ 0.74 | conventional "excellent" agreement |
| App vs rater false-accept rate | ≤ 5% | NUVA (Barbera et al. 2021) |
| App vs rater κ | within one agreement band of rater-rater κ | project design choice |

## Decisions the results drive

- An item with I-CVI below 0.78: revise the cue template (rule-based) or add a validator
  rule that catches its fault (AI-written), then re-audit.
- If AI-written items score below rule-based items on relevance or difficulty fit, turn AI
  personalization off for that exercise type until a revised prompt passes a re-rating.
- Disagreements on the scoring labels: settle by discussion, then update
  `semantic_lexicon.json`, the catalogue's accepted answers, or the classifier, and re-run
  `validate_scoring`.
- Comments on the 6 difficulty-audit items ([difficulty.md](../difficulty.md)): adjust
  their levels in the catalogue.

## Report

Describe the panel (experience, setting), the calibration step, and both sources' CVI
side by side. Say that the scoring benchmark answers were written by the project team, and
that raters were blind to the app's decisions.
