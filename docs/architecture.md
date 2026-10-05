# Architecture

Stroke Recovery AI is a **modular monolith with background workers**. It is a
controlled application pipeline, not an agentic system: every AI call is a single,
bounded, schema-validated request made by deterministic application code.

## System overview

```
Browser ──HTTPS──▶ Next.js (frontend, :3000)
                     │  /api/* rewritten to the backend (same origin → first-party cookie)
                     ▼
                  FastAPI (backend, :8000) ──▶ PostgreSQL   system of record
                     │                     ──▶ Redis        sessions, job queue, rate limits
                     │                     ──▶ S3 / MinIO   ephemeral encrypted audio only
                     ▼
                  ARQ worker ──▶ faster-whisper (STT), analysis, AI generation
                              ──▶ AIProvider (OpenAI first)
```

## Core loop and where safety is enforced

```
exercise ─▶ response (text | speech)
   speech ─▶ encrypted temp object ─▶ STT ─▶ delete audio
         ─▶ deterministic scoring (+ AI semantic analysis where useful)
         ─▶ performance profile update
         ─▶ AI personalization (minimal, pseudonymous context)
         ─▶ schema validation ─▶ clinical constraint validation ─▶ safety validation
              ├─ pass ─▶ ExerciseIssuer ─▶ patient
              └─ fail ─▶ retry (bounded) ─▶ deterministic fallback ─▶ ExerciseIssuer
```

## Key decisions

| Area | Decision | Reason |
|---|---|---|
| Shape | Modular monolith + ARQ worker | Simple to run; module boundaries allow later extraction |
| Worker | ARQ (Redis) over Celery | Async-native, reuses Redis; Celery prefork is unsupported on Windows |
| Auth | Server-side sessions in Redis, opaque HttpOnly cookie | Revocable, no tokens in JS |
| Same origin | Next.js rewrites `/api/*` to FastAPI | First-party `SameSite=Lax` cookie, no credentialed CORS |
| CSRF | SameSite=Lax + Origin check on unsafe methods | Defence in depth without token plumbing |
| Passwords | Argon2id | Current OWASP recommendation |
| DB roles | `sra_migrator` owns schema; `sra_app` DML only | Runtime cannot alter schema or disable safety triggers |
| Constraint enforcement | Single `ExerciseIssuer` service + DB trigger | Two independent layers guard the max-difficulty invariant |
| Constraint versions | Immutable, append-only constraint sets | Every exercise records the exact version it was validated against |
| Audio | App-level AES-GCM before upload; delete after processing; 1-day bucket expiry backstop; versioning off | Encryption independent of provider; deletion is real |
| STT | `SpeechProvider` → `FasterWhisperProvider`, CPU int8 default, GPU optional | Self-hosted; no audio leaves our infrastructure |
| AI | `AIProvider` → `OpenAIProvider`, structured outputs, no chain-of-thought | Provider-independent; auditable via reason codes |
| Picture stimuli | Curated, licensed image bank; AI selects/phrases, never invents images | Clinically reviewable content |
| Scoring | Deterministic first (normalized/synonym/phonological match), AI as secondary signal | Cheap, testable, explainable |
| API contract | TS types generated from FastAPI OpenAPI; Zod at UI boundaries | No hand-maintained drift |
| Local S3 | MinIO via Chainguard image (official free images discontinued) | S3 API is the contract; swappable |

## Backend modules (target)

`core` (config, db, security, logging) · `auth` · `users` · `patients` · `clinicians` ·
`audit` · `clinical` · `exercises` · `sessions` · `responses` · `speech` · `analysis` ·
`performance` · `ai` · `validation` · `storage` · `workers`

Each module owns its models, schemas, service and router. Modules talk through
services, never through each other's tables. Modules are added only when a phase needs them.

## Phases

0. Repository, docs, local infrastructure ✅
1. Foundation: backend/frontend skeletons, auth, RBAC, patient isolation, design tokens
2. Core loop with text input and deterministic exercises (constraint engine before AI)
3. Speech input + STT + scoring + performance profile
4. AI personalization + validation pipeline + fallback + audit
5. Clinician platform
6. Production hardening
