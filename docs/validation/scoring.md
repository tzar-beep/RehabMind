# Scoring validation

Full numbers: [results/scoring.md](results/scoring.md).

## What is scored, and how

Each answer gets two labels:

1. **Outcome** (correct / close / incorrect / skipped), from the deterministic scorer in
   `app/analysis/scoring.py`. This is what the patient sees and what drives progression.
2. **Error type** for picture naming, from `app/analysis/errors.py`. This is information for
   the clinician only. It never changes the outcome.

The error types follow the Philadelphia Naming Test (PNT; Roach et al. 1996), whose decision
tree asks: is the answer a real word, does it sound like the target, is it related in
meaning? ParAlg (Casilio, Fergadiotis et al., JSLHR 2023) automated the same tree from
transcriptions with weighted F1 of 0.87. RehabMind's version is simpler and text-only:

| Type | Example (target "dog") | Rule |
|---|---|---|
| no_response | "", "um", "I don't know" | skipped, hesitation or "can't remember" phrase |
| description | "pet that barks a lot" | 3+ content words without the target (circumlocution) |
| semantic | "cat", "bone", "animal" | real word, same semantic field, superordinate or associate |
| formal | "log" | real word, similar sound, not related in meaning |
| mixed | "duck" | real word, related in both meaning and sound |
| unrelated | "spoon" | real word, neither |
| nonword_related | "dag" | not a word, sounds like the target (typed: often a misspelling) |
| nonword_unrelated | "flimp" | not a word, not like the target |

"Sounds like" is approximated from spelling (same first or last sound, or at least half the
sound string in common, the PNT's lenient criterion). "Real word" uses wordfreq corpus
frequency (Zipf ≥ 2). "Related in meaning" uses a small curated lexicon,
`app/analysis/semantic_lexicon.json`, written for the catalogue's targets and pending SLP
review.

## Benchmark

Two author-labelled sets of typed answers, at least 30 per type in the first:

| Set | Answers | Purpose |
|---|---|---|
| Development | 295 | Written first; the classifier was tuned while looking at it |
| Held-out | 108 | Written after tuning stopped; scored once |

Results (held-out numbers are the honest estimate):

| Measure | Development | Held-out | Target |
|---|---|---|---|
| False-accept rate (wrong answer scored correct) | 1.5% | 1.0% | ≤ 5% (NUVA: 4.9-5.7%) |
| False-reject rate (right answer not accepted) | 0.0% | 0.0% | ≤ 10% |
| Correct/incorrect Cohen's κ | 0.94 | 0.95 | ≥ 0.80 |
| Error-type agreement | 94.9% | 79.6% | — |
| Error-type Cohen's κ | 0.94 | 0.77 | ≥ 0.74 |

The drop from development to held-out (κ 0.94 → 0.77) is the expected cost of tuning on the
development set. The held-out weaknesses are specific:

- **Mixed errors** are rarely recognised (recall 0.08). Many of the held-out "mixed" labels
  are themselves debatable under the PNT rules (is "goat" phonologically similar to "dog"?).
  Settling them is exactly what SLP labelling in Phase 1 is for.
- **Corpus non-words**: wordfreq counts slang and abbreviations ("dag", "tat", "kee") as
  words, so some phonological non-words are called formal errors.
- **"I've forgotten", "I don't remember"** and similar phrases are not yet recognised as no
  response.

The false accepts are catalogue decisions, not scorer bugs: "kitten" is accepted for the cat
photo and "watch" for the clock drawing (which looks like a watch face). Whether these should
count is a name-agreement question for the SLP panel; the catalogue was not changed.

## What this does and does not show

It shows that the code implements the PNT decision tree consistently and that the patient-
facing decision rarely calls a wrong answer correct, on realistic typed answers. It does
**not** show agreement with clinicians (the labels are the authors'), and it says nothing
about spoken answers, where the speech recogniser comes first.

## Spoken answers

Published work found Whisper models write the intended word instead of the error the person
actually said (81% of sound errors in one 2025 study), which would turn errors into false
accepts. RehabMind already transcribes without a prompt or the target word, with voice
activity detection, no conditioning on earlier text, and refuses to score empty, silent,
low-confidence or known-hallucination transcripts (`app/speech/service.py`). New in this
round: a correct answer whose matched word the recogniser was itself unsure of is flagged
`uncertain_speech_match` and shown to the clinician as "check this one". Typed and spoken
accuracy are always reported separately.

Measuring spoken false accepts needs recordings of real or scripted errors: Phase 2
([protocol](protocols/phase2-older-adults.md), part B).
