# Personalization

Full numbers: [results/simulation.md](results/simulation.md).

## The claim, stated so it can be tested

No published aphasia study has separated adaptive difficulty from extra practice time, so
"personalization improves recovery" is not something any app has shown. The testable chain
is: personalization keeps practice at a productive difficulty and sustains engagement →
more practice → better naming of practised words. RehabMind tests the first link now, in
simulation, and provides the tools to test it with people (Phases 2-3).

**Productive band**: the learner's true chance of answering correctly is 60-90%. This band
is a design choice informed by the "85% rule" (Wilson et al. 2019, itself a simulation
result) and the challenge-point framework, not an established aphasia target.

## Simulation

`app/scripts/simulate_learners.py` gives 300 synthetic learners (ability ~ N(0, 1.5)) 300
exercises each, under four policies. The step rule and ability-guided policies call the
app's own progression code.

| Policy | What it does |
|---|---|
| fixed-easy | always the clinician's minimum level |
| fixed-middle | always the middle of the range |
| step-rule | RehabMind's original rule: up after 3 correct, down after 2 wrong |
| ability-guided | after 10 answers, the level the learned ability estimate predicts ~80% success at |

Share of exercises in the productive band:

| Scenario | fixed-easy | fixed-middle | step-rule | ability-guided |
|---|---|---|---|---|
| Stable ability | 41% | 38% | 45% | **71%** |
| Improving over time | 30% | 43% | 56% | **76%** |
| Declining over time | 44% | 29% | 38% | **64%** |
| Levels steeper than the model assumes | 29% | 38% | 46% | **71%** |
| Noisy items within a level | 38% | 36% | 44% | **59%** |
| Narrow clinician range (2-3) | 44% | 38% | 47% | **55%** |

Ability-guided progression also roughly halves runs of three wrong answers in a row (7.0 vs
12.6 per 300 exercises, stable scenario).

**Finding:** the original step rule is only slightly better than fixed difficulty. It
reaches its next level quickly but then oscillates, leaving 35% of exercises too hard. Using
the ability estimate the app was already computing (but only showing to clinicians and the
LLM) is the larger improvement.

## What changed in the app

Clinicians can now choose **ability-guided** progression in the practice limits
(`progression_mode` on the constraint set). It is opt-in, versioned like every other limit,
and always clamped to the clinician's range. The issuer and the database trigger enforce the
range exactly as before. The step rule remains the default.

## Limits

The learners follow a logistic model, the same family the app's estimator assumes. The
"steeper levels" and "noisy items" scenarios test robustness to that assumption, but real
patients have bad days, fatigue and learning effects the model does not include. This shows
the algorithm *can* keep practice in band, not that patients benefit. That needs Phase 2
(engagement and "just right" ratings, healthy older adults) and Phase 3 (people with
aphasia).
