# Dry run of Phases 1-3 with simulated participants

> **Synthetic data, not evidence about people.** No clinician, older adult or person with
> aphasia took part in anything on this page. Every rating, answer and recording here was
> produced by a model written for the purpose. These runs test the *study machinery* and
> show how the app behaves under realistic assumptions; they do not replace the studies in
> [protocols/](protocols/), and none of these figures may be quoted as clinical results.

Phases 1-3 need people and ethics approval (see [README.md](README.md)). While those are
arranged, each phase was run end to end with stand-ins, through the same code, packets and
analysis scripts the real studies will use. A dry run like this finds problems in the
protocol and the software before anyone's time is spent, which is what happened: Part B
found a speech-recogniser problem that changed the app.

| Phase | Stand-in for participants | Result | What it changed |
|---|---|---|---|
| 1: clinician panel | 3 language-model raters (Qwen2.5-3B, SLP personas), blind to source | Not usable as a panel: every item rated 4/4; raters agree at κ = 0.48 | Confirms the panel must be human |
| 2A: usability tasks | Automated browser, phone and laptop | Every protocol task completes; no target under 44 px; no WCAG 2.1 AA violations | A permanent e2e test |
| 2B: speech fidelity | 4 synthetic voices × 40 scripted answers | **16% of sound errors heard as the target word**, none flagged uncertain | Spoken matches no longer raise difficulty |
| 2C: mode comparison | 12 simulated older adults, 8 sessions, ABBA/BAAB | Ability mode: fewer too-hard items (4% vs 11%) but no gain in the productive band | Ability mode is not recommended for near-ceiling users |
| 3: single-case study | 4 simulated people with aphasia, 24 sessions, alternating | Ability mode: more practice in the productive band (57% vs 51%), fewer too-hard items (16% vs 24%) | Supports running Phase 3 as designed |

## Phase 1: language-model raters

`app/scripts/simulate_panel.py` gives the 48 content items and 200 answers from
[review-packets/](review-packets/) to three rater personas, with the instructions and
scales the panel gets. Results: [results/phase1-simulated.md](results/phase1-simulated.md).

- **Content validity.** All three raters gave every item 4 for relevance, clarity and tone,
  AI-written and rule-based alike (S-CVI/Ave 1.00 for both). A rater who never
  discriminates gives no information: this is the leniency of a small model as judge, not
  evidence that the items are good. The one dimension with spread, difficulty fit (means
  3.07 AI, 3.04 rule-based), shows no difference between sources.
- **Scoring.** The two raters agree with each other at κ = 0.48 on correct/incorrect and
  κ = 0.32 on error type, far below the 0.74 the protocol requires of human raters. The
  app agrees with rater A at κ = 0.86 (false accepts 2.2%) and with rater B at κ = 0.42.

So the dry run validates the packets and the analysis, and shows that a cheap substitute
for SLP raters does not exist at this model size. The panel remains the next step.

## Phase 2

### Part A: usability tasks

`frontend/e2e/usability.spec.ts` performs the protocol's tasks in order (sign in, start,
use a hint, answer three pictures, stop early and come back, finish and rate) on a 390 px
phone and a 1280 px laptop. It checks a step budget for each task, a 44 px minimum for every
button and link, and axe WCAG 2.1 AA rules on each screen. Both pass and run in CI. What
needs people: the System Usability Scale and the open questions.

### Part B: speech recogniser fidelity

`app/scripts/speech_fidelity.py` builds the protocol's 40 scripted answers from the
catalogue (10 correct, 10 related words, 10 real-word sound errors such as "mat" for cat,
10 non-word sound errors such as "belescope" for telescope), speaks each with two Windows
voices at normal and slow rates, and passes the audio through the production recogniser
(faster-whisper `small.en`, no prompt). Results:
[results/speech-fidelity-simulated.md](results/speech-fidelity-simulated.md).

| Scripted | Repaired into the target (false accept) |
|---|---|
| Related word | 0% |
| Real-word sound error | 5% |
| Non-word sound error | **28%** |

Sound errors overall: 16.2%, over the protocol's 5% limit. The uncertainty flag caught
none of the repaired non-words: the recogniser was confident. Synthetic voices are clearer
than older or aphasic speech, so real speakers are likely to fare worse, not better.

**Change made.** Following the protocol's rule, a spoken answer matched to the target now
counts as "close" for progression and for the ability estimate, like a correct answer after
a hint: it holds the level instead of raising it (`counted_outcome` in
`app/performance/ability.py`). The patient still sees it as correct, and the practice
limits page tells the clinician. The setting `SPEECH_COUNTS_FOR_PROGRESSION` turns full
credit back on once a real Part B run passes.

**Second change: the patient confirms a match.** When a spoken answer would score as
correct, the app now asks "I heard “door”. Is that what you said?" (with a button to hear
the word) before scoring it. "No, try again" discards it and keeps the exercise open; the
count of rejections is a running measure of mishearings in real use. Wrong words are
scored at once, with no extra question. This relies on the patient noticing the
difference, which not everyone with aphasia can, so the progression rule above stays.

### Part C: progression mode comparison

`app/scripts/simulate_participants.py phase2`: 12 simulated adults aged 60+ (high naming
ability, errors mostly tip-of-the-tongue and related words), 8 sessions of 10 pictures,
levels 1-5, mode switched by a new constraint version before each session in ABBA or BAAB
order. Results: [results/phase2-simulated.md](results/phase2-simulated.md).

| Mode | Answers | Accuracy | True chance in productive band | Too hard (< 50%) | Rated just right |
|---|---|---|---|---|---|
| Step rule | 480 | 76% | 59% | 11% | 73% |
| Ability-guided | 480 | 84% | 57% | 4% | 67% |

For people near the top of the scale, ability mode removes most too-hard items but makes
practice easier rather than better targeted, and slightly fewer sessions feel "just right".
Healthy adults are the wrong group to show a benefit, which the protocol anticipates; their
part is usability and speech fidelity.

## Phase 3: single-case study

`app/scripts/simulate_participants.py phase3`: 4 simulated people with aphasia with
different profiles (mild and moderate anomic, moderate conduction with mostly sound errors,
moderate-severe mixed), 24 sessions of 20 pictures with the mode alternating in random
order within pairs of sessions, 10% of sessions missed, a chance of stopping early after
three misses in a row. Practice is limited to four picture categories; the other four are
unpractised controls. Naming probes (no hints, no feedback) at baseline (×3), weekly, after
treatment and at maintenance. Results: [results/phase3-simulated.md](results/phase3-simulated.md).

| Mode | Sessions | Accuracy | True chance in productive band | Too hard (< 50%) | Rated just right |
|---|---|---|---|---|---|
| Step rule | 42 | 64% | 51% | 24% | 71% |
| Ability-guided | 44 | 71% | 57% | 16% | 80% |

Per participant, session accuracy under ability mode beat the step rule clearly for the
mild anomic (NAP 0.93) and conduction (0.97) profiles, was similar for the moderate anomic
profile (0.55) and lower for the moderate-severe mixed profile (0.40). For that profile
both modes gave the same average true chance of success (59%), so the difference is noise
across about ten sessions per mode: single-case comparisons need the protocol's full
length and replication across participants. (The results
table lists participants by pseudonym: P-1e32… mild anomic, P-ad74… conduction, P-4564…
mixed, P-8fa1… moderate anomic.) Probe accuracy
on practised pictures rose from baseline for all four (NAP 0.83-1.00); unpractised controls
did not rise consistently. 86 of 96 planned sessions were done and 5 stopped early.

These numbers follow from the learner model by construction: practised pictures get easier
with each exposure, so practised probes must rise. What the run does test is the app's
side: that ability mode, faced with learners whose difficulty differs from the catalogue
levels, finds a better level than the step rule for most profiles, and that the export and
analysis produce the per-participant tables the protocol needs.

## How the simulated participants work

- **Ability and difficulty.** Each participant has a hidden ability. Each picture has a
  true difficulty from its word frequency, length and BOSS name agreement, plus personal
  noise, so the app's five levels only approximate what is hard for each person.
- **Answers.** The chance of naming a picture is logistic in ability minus difficulty. A
  wrong answer is a real string the app scores itself: a word from the same semantic
  field, a one-sound slip, a description ("you use it to read"), an unrelated word, or "I'm
  not sure". Struggling participants ask for hints.
- **Ratings.** After each session: "too easy" above about 92% accuracy, "too hard" below
  about 55%, with noise.
- **The app is real.** Participants practise through `app.sessions.service`, the code the
  API runs, with the configured AI provider choosing pictures, the clinician's limits
  enforced, and difficulty moved by the progression rule under test.

Accounts are named `sim-<phase>-<tag>-NN@study.invalid` and exist only in the local
development database. The script refuses to run outside development.

## Reproduce

```bash
cd backend
uv run python -m app.scripts.simulate_panel
uv run python -m app.scripts.analyse_panel analyse --panel simulated/panel --report phase1-simulated.md
uv run python -m app.scripts.speech_fidelity --write
uv run python -m app.scripts.simulate_participants phase2 --tag r3
uv run python -m app.scripts.simulate_participants phase3 --tag r3
cd ../frontend && npx playwright test e2e/usability.spec.ts
```

Raw data: [simulated/](simulated/) (per-answer logs with each participant's true chance of
success, session lists, probes, and the pseudonymised study exports).
