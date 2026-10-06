# AI pipeline

Generative AI has three bounded jobs (see [review2-genai.md](review2-genai.md) for the full
write-up): personalize the next exercise's wording for picture naming, sentence construction
and picture description (`exercise_generation_v1`), write a short supportive tip after an
answer is scored (`feedback_generation_v1`), and draft a clinician progress summary
(`progress_summary_v1`). The real model is a local transformer LLM served by **Ollama**
(default `qwen2.5:3b`).

It is a fixed application pipeline — **not an agent**: one bounded call per attempt, no
tools, no planning, no memory, no autonomous decisions. Clinician constraints always win.

```
issue_next()
  └─ build_input()            minimal, pseudonymous: objective, difficulty range, target level,
  │                           last 10 outcomes, recent accuracy, learned ability estimate and
  │                           trend, weakest category, ≤12 candidate pictures
  │                           (no names, emails, user/patient IDs, or patient free text)
  └─ for attempt in 1..2:
        provider.generate()   AIProvider interface; AI_TIMEOUT_S (default 20 s)
        check_schema()        exact JSON shape, extra fields forbidden, enum reason code
        check_clinical()      picture ∈ candidates, difficulty matches picture and range,
                              category allowed
        check_safety()        no answer leak, no medical/recovery claims, no pressure
                              language, no links/digits, short plain wording, valid
                              first-sound cue
        → accept: Proposal(source="ai") → ExerciseIssuer (validates again) → DB trigger
        → reject/error: audited, retry
  └─ deterministic rules proposal → most conservative fallback (minimum difficulty)
```

The patient is never blocked by AI failure.

## What the AI decides (and what it cannot)

| AI may | AI may not |
|---|---|
| choose one picture from the clinician-bounded candidate list | invent pictures or words |
| phrase the question (≤ 8 words) | change difficulty range, types, modes or categories |
| write a meaning cue and a first-sound cue (naming) or one hint (sentence, description) | diagnose, predict recovery, or give advice |
| write feedback on an answer after it is scored | change, restate or contradict the score |
| draft a clinician summary from supplied figures | invent numbers (rejected by validation) |
| return a structured rationale code | return free-text reasoning (schema forbids it) |

Rationale codes: `reinforce_recent_error`, `consolidate_success`, `introduce_new`,
`category_variety`.

## Audit (`ai_generations`, append-only)

Per attempt: task (`exercise.personalize`, `feedback.generate`, `progress.summarize`),
provider, model, model version, prompt version, token usage, constraint
set + version, input snapshot, raw output (truncated), parsed output, status
(`accepted` / `rejected` / `error`), failed stage (`provider` / `schema` / `clinical` /
`safety` / `issuer`), reason codes, latency, and the exercise it produced.
Clinicians read it at `GET /api/v1/patients/{id}/ai-generations` and, grouped per exercise slot
(result: accepted / accepted after retry / rule-based used), at `.../ai-generations/runs`,
shown in the clinician **AI audit log** (assigned patients only).
Chain-of-thought is neither requested nor stored.

## Providers

| `AI_PROVIDER` | Behaviour |
|---|---|
| `ollama` | `OllamaAIProvider`: real local LLM. One `POST /api/chat` per attempt with the task's JSON Schema as `format` (schema-constrained decoding), `stream: false`, temperature 0.4. Unreachable server, HTTP errors and empty replies raise `AIProviderError` → retry → fallback. `GET /api/v1/ai/status` reports whether the model is ready. |
| `fake` (default) | `FakeAIProvider`: offline, deterministic, $0. Personalizes from the input and injects `AI_FAKE_FAULT_RATE` (default 0.2) faulty outputs — malformed JSON, out-of-range difficulty, invented picture, unsafe wording, answer leak, extra "reasoning" field, timeout — so validation, retry, fallback and audit are visible in demos. |
| `none` | AI off; rules only. |

Adding another provider = one class implementing
`AIProvider.generate(GenerationRequest) -> GenerationResult` plus a settings value. The request
carries the system prompt, user prompt and JSON Schema for structured output. Every output
still passes the same validation.
For slower real models, generate the next exercise in the worker while the patient answers
the current one.

## Cues and progression

Hints are revealed on request: meaning first, then first sound. A correct answer after a
hint counts as correct for the patient but **holds** the difficulty level (cued, not
independent naming).
