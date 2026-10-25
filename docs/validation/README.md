# Clinical validation

An industry reviewer's main recommendation was:

> The major area for improvement is clinical validation, demonstrating that the generated
> exercises and scoring are appropriate for aphasia rehabilitation and that personalization
> actually improves the patient's training experience.

This folder is the answer: what RehabMind now claims, the evidence for each claim, and the
studies (with their materials ready) that would turn the remaining open claims into
evidence. The background literature review is in [research/roadmap.md](research/roadmap.md).

## The three questions and where they stand

| Question | What we can show now (Phase 0, no participants) | What needs people |
|---|---|---|
| Is the **scoring** appropriate? | Right/wrong decisions agree with labelled answers (held-out κ = 0.95, 1.0% false accepts). Errors are classified with the Philadelphia Naming Test categories (held-out κ = 0.77). [scoring.md](scoring.md) | Two speech and language therapists (SLPs) label 200 answers: Phase 1 |
| Are the **generated exercises** appropriate? | Difficulty levels agreed with word-frequency norms (ρ = 0.84) but not with BOSS name agreement, so they were rebalanced to include it. The validators stop every leaked answer, wrong first-sound cue and unsafe text: 14.7% of raw model outputs leaked the answer and 23.3% of feedback called a wrong word "nearly right" (0% after the v2 feedback prompt); none reached a patient. [difficulty.md](difficulty.md), [genai.md](genai.md) | SLP panel rates AI vs rule-based items for content validity (CVI): Phase 1 |
| Does **personalization** improve training? | In simulation, the new ability-guided mode keeps 71% of practice in the productive band vs 45% for the step rule and 38-41% for fixed difficulty. [personalization.md](personalization.md) | Healthy older adults (Phase 2), then people with aphasia in a single-case study (Phase 3) |

## Claims we make, and claims we do not

Each claim is tied to the evidence that supports it. Nothing here says RehabMind improves
recovery.

**Supported now (Phase 0):**

- "Typed-answer scoring agrees with labelled answers at κ = 0.95 on a held-out set, with a
  false-accept rate of 1.0%" (author-labelled, synthetic answers; SLP labels pending).
- "The validation layer reduces patient-facing answer leaks from 14.7% of raw model outputs
  to 0%."
- "In simulation, ability-guided progression keeps learners in the productive difficulty band
  more often than the step rule or fixed difficulty, across six scenarios."

**After Phase 1:** "SLPs rated generated exercise text as relevant (S-CVI/Ave = …) and no
worse than the rule-based text", and "the scorer agrees with SLPs as well as SLPs agree with
each other".

**After Phase 3 only:** "In n = … participants, sessions run with ability-guided progression
gave … compared with the step rule."

**Never claimed:** effects on conversation, functional communication or recovery; anything
about spoken answers beyond "the recogniser heard the target word". RehabMind is a research
prototype, not a medical device.

## Phases

| Phase | Status | Ethics | What is in the repo |
|---|---|---|---|
| **0: Technical validation** | Done | None needed | Scoring benchmark, PNT error classifier, difficulty audit, GenAI audit, learner simulation, plain-language checks, speech-uncertainty flag. Results in [results/](results/) |
| **1: Expert panel** | Dry run done; ready to run with SLPs | Institutional ethics committee (IEC), exempt or expedited review | [Protocol](protocols/phase1-slp-panel.md), blinded [rating packets](review-packets/), [analysis script](../../backend/app/scripts/analyse_panel.py) |
| **2: Healthy older adults** | Dry run done; ready to run | IEC expedited review | [Protocol](protocols/phase2-older-adults.md), usability e2e test, speech-fidelity script, after-session rating, pseudonymised [export and analysis](../../backend/app/scripts/study_data.py) |
| **3: People with aphasia** | Dry run done; needs a clinical partner | Full IEC review | [Protocol](protocols/phase3-single-case.md), progression-mode switch per constraint version, the same export and analysis |

**Dry runs with simulated participants** ([simulated.md](simulated.md)). Every phase was run
end to end with stand-ins (language-model raters, synthetic voices, simulated learners
practising through the app's own session code) to test the study machinery before people
are involved. Their figures are synthetic and are not evidence about people. They found
one real problem: the speech recogniser turned 16% of scripted sound errors into the target
word, so spoken matches no longer raise difficulty until a real Part B run passes.

Consent materials and the ethics application outline: [protocols/ethics-and-consent.md](protocols/ethics-and-consent.md).

## What changed in the app

| Change | Where | Why |
|---|---|---|
| PNT-style **error type** for every naming answer, shown to clinicians (session detail, overview) | `app/analysis/errors.py` | Clinicians think in semantic vs phonological errors, not "incorrect" |
| **Uncertain speech match** flag: correct, but the recogniser was unsure of that word | `app/sessions/service.py` | Speech recognisers tend to "hear" the expected word; these answers need a check |
| **Plain-language checks** on AI text: rare words, long sentences, patronising tone | `app/validation/plain_language.py` | Aphasia-friendly information guidance |
| **Ability-guided progression** (clinician opt-in per constraint version) | `app/performance/progression.py` | Simulation showed it keeps practice in the productive band; also the condition switch for Phases 2-3 |
| **After-session rating** "Too easy / Just right / Too hard" (pictorial, optional) | patient practice screen; clinician overview and sessions | The patient's own report of whether difficulty was right |
| **Spoken matches hold the level** (and cued successes, in the ability estimate too) until speech is validated | `app/performance/ability.py` `counted_outcome` | Dry run of Phase 2 part B: 16% of sound errors were heard as the target |

## Reproduce everything

```bash
cd backend
uv run python -m app.scripts.validate_scoring --write
uv run python -m app.scripts.audit_difficulty --write
uv run python -m app.scripts.simulate_learners --write
uv run python -m app.scripts.genai_audit --write      # needs Ollama with the configured model
uv run python -m app.scripts.analyse_panel packets    # blank rating packets for Phase 1
```

`tests/test_validation.py` keeps the published numbers from silently getting worse: the
benchmark thresholds and the simulation's main comparison are asserted in CI.
