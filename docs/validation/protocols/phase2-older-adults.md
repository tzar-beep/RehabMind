# Phase 2 protocol: healthy older adults

**Aim.** Before involving people with aphasia, check with healthy adults aged 60 and over
(A) that the patient screens are usable, (B) whether the speech recogniser writes down
errors faithfully or "repairs" them, and (C) whether ability-guided progression feels
better pitched than the step rule.

**This is not an aphasia sample.** Results speak to usability, the speech pipeline and the
progression mechanics, never to therapy benefit.

**Ethics.** Minimal risk; IEC expedited review ([ethics-and-consent.md](ethics-and-consent.md)).

## Participants

- 12-20 adults aged 60+, no diagnosed language disorder, normal or corrected vision and
  hearing, English as a language of daily use.
- Exclude: current speech or language therapy, diagnosed dementia.
- Recruit through senior citizens' associations, family networks or university staff
  retirees. One session of about 60 minutes in person, plus 2 weeks of home use for Part C.

## Part A: usability (in person, 20 minutes)

Tasks, in order, on a laptop or tablet: sign in; start practice; answer three pictures by
typing; answer three by speaking; use a hint; finish and give the difficulty rating; stop
early and come back. Record task success, errors and time. Then the System Usability Scale
(SUS; read aloud if preferred) and two open questions: "What was hardest?", "What would you
change?".

Target: SUS ≥ 68 (average usability), every task completed by at least 80% of participants.

## Part B: speech recogniser fidelity (in person, 20 minutes)

Each participant reads aloud a scripted list of 40 naming responses for pictures shown on
screen: 10 correct names, 10 related words ("cat" for dog), 10 sound errors that are real
words ("log"), and 10 sound errors that are not words ("dag"). Use the speech answer
in the app with a study account whose constraint set allows speech.

For each recording, compare what the app transcribed with what was scripted:

| Outcome | Meaning |
|---|---|
| Faithful | transcript matches the scripted response |
| Repaired | transcript is the target word although an error was scripted (a false accept) |
| Other | anything else |

Report the repaired rate for each error kind, and how many repaired answers carried the
`uncertain_speech_match` flag. A repaired rate above 5% for sound errors means spoken
answers should not count towards progression until fixed (for example a larger Whisper
model, or confirming flagged answers with the patient).

The scripted lists live in the study folder, not in the app. Audio is deleted after
transcription as usual; only transcripts and scores are kept.

## Part C: progression mode comparison (2 weeks at home)

Alternating-treatments design within each participant:

- Constraint set: picture naming only, levels 1-5 (healthy adults will be at ceiling on easy
  items, so the full range is needed), 15 pictures per session.
- 8 sessions over 2 weeks. The study lead switches `progression_mode` between `step` and
  `ability` before each session, in a randomised order fixed in advance (for example
  ABBA BAAB), so each participant has 4 sessions of each.
- After every session the participant gives the in-app rating (too easy / just right / too
  hard).

Outcomes per mode: share of sessions rated "just right" (primary), share of answers in the
productive band, accuracy, sessions completed vs stopped early.

```bash
cd backend
uv run python -m app.scripts.study_data export --salt "$STUDY_SALT" --out phase2.csv --patients <ids>
uv run python -m app.scripts.study_data analyse phase2.csv
```

The salt is a secret held by the study lead; the export contains pseudonyms, study days and
scores only.

## Expected limitations

Healthy adults rarely make errors on common objects, so the step rule will push most of them
to level 5 and the comparison will be compressed. That is acceptable: Part C mainly checks
that the modes behave as designed and that the rating is understood.
