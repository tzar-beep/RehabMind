# Prompt engineering in RehabMind

Prompts are treated as code here: versioned, tested, logged with every output, and changed
only when a measurement says the change helps. This page covers what the prompts do, how they
were improved, what the evidence shows, and what it does not show.

Code: [`backend/app/ai/prompts.py`](../backend/app/ai/prompts.py). Study:
[`backend/app/scripts/prompt_study.py`](../backend/app/scripts/prompt_study.py). Full results:
[validation/results/prompt-study.md](validation/results/prompt-study.md).

## The result

Same model (`qwen2.5:3b`), same requests, same validators. Only the prompt changes. These are
117 requests per prompt on pictures that were kept out of prompt development.

| Prompt | What it adds | Valid first time | Valid after one retry |
|---|---|---|---|
| Naive, no schema | One line asking for JSON | 0% (0-3) | 0% (0-3) |
| Naive + JSON Schema | Structured output | 2% (0-6) | 3% (1-7) |
| `exercise_generation_v1` | Role, context, constraints, safety, type-specific rules | 61% (52-69) | 75% (67-82) |
| `exercise_generation_v2` | Supplied facts, contrastive examples, self-check, tighter schema | **83% (75-89)** | **93% (87-96)** |

Brackets are 95% confidence intervals. When an output is rejected twice, the app uses
rule-based text instead, so v2 cuts that from about 25% of requests to about 7%. Median
latency did not get worse (1.1 s to 1.0 s) despite the longer prompt.

The prompt changes fixed specific failures (share of raw outputs, held-out pictures):

| Rejection | v1 | v2 | What changed it |
|---|---|---|---|
| Wrong first-sound cue | 21.5% | 0% | The app supplies `first_letters` |
| Too long | 22.7% | 6.6% | Examples show the length; self-check |
| Gave away the answer | 16.6% | 10.9% | The app supplies `avoid_words`; bad example |
| Uncommon word | 3.1% | 5.1% | Not improved |

### Where it did not work

**Picture description is not clearly better.** It rose from 45% to 67% on the development
pictures but fell from 71% to 52% on the held-out ones, with only 21 requests per prompt
there. Across both sets it is about 56% to 61%, and the intervals overlap, so there is no
evidence of a real improvement. The other two types carried the overall gain (naming 57% to
89%, sentence building 62% to 90%). The model cannot see the photo, so it guesses from the
picture's file name. See [Next step](#next-step).

## Techniques, and where to find them

| Technique | What it does here | Where |
|---|---|---|
| Role prompting | "You are RehabMind's … assistant. You are not a medical diagnostician." | `EXERCISE_SYSTEM` |
| Message separation | Stable rules go in the system message, per-request data in the user message | every `*_prompts()` |
| Context injection | Objective, recent accuracy, learned success probability, trend, weakest category | `_performance()` |
| Constraint framing | Says what the app has already decided, so the model cannot reopen it | "The application has already decided…" |
| Task decomposition | Numbered steps with word limits | `EXERCISE_USER` |
| Instruction routing | Different rules per exercise type and per scored outcome | `_HINT_RULES`, `_OUTCOME_TASK` |
| Contrastive few-shot | One good and one bad example, on a picture that is never a candidate | `_EXAMPLES` |
| Supplying facts | Hands over the first letters and banned words rather than asking the model to work them out | `prompt_facts()` |
| Self-check | A short checklist just before the output instruction | "CHECK before answering" |
| Structured output | A JSON Schema constrains decoding, and the picture is limited to this request's candidates | `exercise_schema()` |
| Injection defence | A patient's answer is quoted data, flattened to one line so it cannot pose as a new section | `feedback_prompts()` |
| Pre-computed labels | The model gets "high/moderate/low accuracy", not a percentage to judge | `level()` |
| Data minimisation | No names, emails or IDs reach a prompt | `build_input()` |
| Versioning | Every call logs its prompt version, so any output traces to its exact prompt | `ai_generations` |

The most useful finding: **do not ask a small model to do what the app can compute.** Telling
the model the first letter removed a whole failure class. No amount of instruction wording
had managed that in v1.

### Deliberately not used

- **Chain-of-thought.** It adds latency to a call a patient is waiting on, and free-text
  reasoning would be one more thing to validate. The schema forbids it.
- **Agents or tools.** The model makes one bounded call and cannot act. See
  [ai-pipeline.md](ai-pipeline.md).
- **Prompts as the safety layer.** A prompt asks; validators enforce. The prompts lower how
  often output gets rejected, and they are not what keeps a patient safe.

## How the prompts were improved

Each version answers a problem that was observed, not a guess.

| Version | Problem found | Change | Measured effect |
|---|---|---|---|
| `feedback_generation_v2` | The model called different words "nearly right" | One instruction and one example per outcome | Valid first time 31% to 79% |
| `feedback_generation_v3` | Tips described pictures wrongly | States the model cannot see the picture; asks for a clue about meaning | 88% valid; wrong clues still got through, so those tips were removed from the app |
| `exercise_generation_v2` | About 30% of requests fell back to rules | Everything in the table above | 61% to 83% first time on held-out pictures |
| `feedback_generation_v4` | An example said "the picture shows one", contradicting v3's own rule; an answer with line breaks could imitate a prompt section | Fixed the example; answers flattened to one line | 94% first time, 96% after retry, no score contradictions. Compared with v3's 88% and 98%, this is not a clear change: v4 fixes defects and was not expected to raise the rate |

## Method

`prompt_study.py` sends identical requests under each prompt and runs every output through
the production validators with the production retry. Temperature and options match production.

Pictures are split in two by a hash of their name. The prompts were revised using only the
development half (147 requests per prompt), then the wording was frozen and the held-out half
(117) was run once. The picture description drop above was found in that run and was left as it is,
because adjusting the prompt after seeing it would invalidate the held-out test.

Reproduce it (needs Ollama and the model):

```bash
cd backend
uv run python -m app.scripts.prompt_study --split test --write
```

The earlier prompts stay frozen in
[`prompt_archive.py`](../backend/app/ai/prompt_archive.py) so this comparison stays runnable.

## What this evidence does not show

- **Valid is not true.** Validators check form, safety and leaks, not meaning. A cue can pass
  and still be wrong. Only clinicians can judge that: see the
  [panel protocol](validation/protocols/phase1-slp-panel.md), which has not been run.
- **No patient has used this.** Nothing here measures whether the prompts help anyone recover
  or practise more.
- **The naive prompts are a floor, not a fair rival.** They never see the word limits the
  validators enforce, so they are expected to fail. The v1 to v2 comparison is the meaningful one.
- **Intervals are slightly optimistic.** Each picture is requested three times, so requests
  are not fully independent.
- **Copying.** 8 of 109 accepted v2 outputs reused wording from an example, such as "Start
  with who is doing it". These are generic hints that still fit, but the variety is lower.
- **One model, one run.** Results apply to `qwen2.5:3b` at temperature 0.4.

## Next step

Picture description should stop asking the model for what it cannot know. The patient always
sees a fixed question, so the generated `prompt` field is never shown, yet it still causes
rejections (leaks and length). Removing it from the output, or choosing the hint from a fixed
list, should address this directly. That would be `exercise_generation_v3`, tested the same
way on freshly split pictures.

## See it in the app

Set `AI_PROVIDER=ollama` and `AI_DEMO_VIEW=true`, then open a patient's **AI pipeline** as a
clinician. The prompt step labels each part of the real prompt (objective, context,
constraint, task, few-shot, self-check, format) and shows the full text sent to the model.
