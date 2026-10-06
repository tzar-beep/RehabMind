#  RehabMind

**AI-assisted, clinician-bounded speech and language practice for people recovering from
stroke-related aphasia.**

![Next.js](https://img.shields.io/badge/NEXT.JS-16-000000?style=for-the-badge&logo=nextdotjs&logoColor=white&labelColor=555)
![FastAPI](https://img.shields.io/badge/FASTAPI-PYTHON%203.12-009688?style=for-the-badge&logo=fastapi&logoColor=white&labelColor=555)
![PostgreSQL](https://img.shields.io/badge/POSTGRESQL-18-4169E1?style=for-the-badge&logo=postgresql&logoColor=white&labelColor=555)
![Redis](https://img.shields.io/badge/REDIS-SESSIONS%20%7C%20JOBS-DC382D?style=for-the-badge&logo=redis&logoColor=white&labelColor=555)

![Speech](https://img.shields.io/badge/SPEECH-FASTER--WHISPER%20(LOCAL)-6A1B9A?style=for-the-badge&labelColor=555)
![AI](https://img.shields.io/badge/GEN%20AI-VALIDATED%20%7C%20AUDITED%20%7C%20NON--AGENTIC-0B7A75?style=for-the-badge&labelColor=555)
![Security](https://img.shields.io/badge/SECURITY-RBAC%20%7C%20CSP%20%7C%20AES--GCM-4CAF50?style=for-the-badge&labelColor=555)

![Accessibility](https://img.shields.io/badge/ACCESSIBILITY-WCAG%202.1%20AA-1565C0?style=for-the-badge&labelColor=555)
![Tests](https://img.shields.io/badge/TESTS-PYTEST%20%7C%20VITEST%20%7C%20PLAYWRIGHT-E67E22?style=for-the-badge&labelColor=555)
![Cost](https://img.shields.io/badge/COST-%240%20%7C%20NO%20API%20KEYS-2E7D32?style=for-the-badge&labelColor=555)
![Status](https://img.shields.io/badge/STATUS-ACADEMIC%20PROTOTYPE-9E9E9E?style=for-the-badge&labelColor=555)

Patients name pictures by **speaking or typing**. RehabMind transcribes speech on its own
server, scores each answer, and personalizes the next exercise, always **inside limits set
by the patient's clinician**. Clinicians see real practice data, manage those limits as
versioned settings, and can audit every AI decision.

> ⚠️ Academic / research prototype. Not a diagnostic tool, not clinically validated, and
> not an autonomous system: the clinician is always the authority.

---

## 📸 Screenshots

| Patient: picture naming with hints | Patient: supportive feedback |
|---|---|
| ![Practice with hints](docs/images/practice-hints.png) | ![Feedback](docs/images/practice-feedback.png) |

| Clinician: patient overview & trends | Clinician: versioned practice limits |
|---|---|
| ![Overview](docs/images/clinician-overview.png) | ![Constraints](docs/images/clinician-constraints.png) |

<details>
<summary><b>Clinician: AI audit log</b></summary>

![AI audit log](docs/images/clinician-ai-log.png)
</details>

---

## ✨ Highlights

| 🧑‍🦽 Patients | 🩺 Clinicians | 🛡️ Safety by design |
|---|---|---|
| Real-world photos (61, openly licensed) plus line drawings | Dashboard of assigned patients (real data only) | `MAX_DIFFICULTY` enforced in 4 independent layers, incl. a DB trigger |
| Answer by **voice or typing**; naming, sentence building, picture description | Accuracy & difficulty trends, session history | Generative AI is bounded: schema → clinical → safety validation |
| Hints: meaning first, then first sound | **Versioned practice limits** (never edited, only superseded) | Retry + deterministic fallback; patients are never blocked |
| Warm, honest feedback with the correct word | **AI audit log**: suggestion, verdict, what the patient got | Audio **encrypted → transcribed locally → deleted** |
| Large targets, legible font, reduced motion | Transcript confidence, never raw audio | Whisper hallucinations are never scored |

---

## 🏗️ Architecture

```mermaid
flowchart LR
    B([Browser]) -- HTTPS --> C[Caddy<br/>TLS · HSTS]
    C --> W[Next.js 16<br/>UI · CSP nonce]
    W -- /api --> A[FastAPI<br/>RBAC · sessions]
    A --> P[(PostgreSQL<br/>roles · triggers)]
    A --> R[(Redis<br/>sessions · queue)]
    A --> M[(MinIO<br/>encrypted audio)]
    R --> K[ARQ worker]
    K --> S[faster-whisper<br/>local STT]
    K --> M
    A --> AI[AI provider<br/>validated · audited]
    AI --> OL[Ollama · local LLM<br/>qwen2.5:3b transformer]
```

Modular monolith plus a background worker. Only Caddy is exposed. The API, database, cache and
storage are internal.

## 🔁 Core practice loop

```mermaid
flowchart TD
    E[Exercise shown<br/>objective → exercise type] --> R{Patient answers}
    R -- types / taps --> NLP[NLP analysis<br/>normalise · fuzzy match · concepts · word order]
    R -- speaks --> ENC[Encrypt audio] --> STT[DL: faster-whisper<br/>local speech-to-text] --> DEL[Delete audio]
    DEL --> REL{Transcript reliable?}
    REL -- no --> E
    REL -- yes --> NLP
    NLP --> SC[Deterministic score<br/>final, never changed by AI]
    SC --> FBK[GenAI feedback<br/>prompt feedback_generation_v1]
    SC --> PERF[Performance profile +<br/>ML ability estimate]
    PERF --> POL[Difficulty policy<br/>clamped to clinician range]
    POL --> CTX[Structured patient context]
    CTX --> PR[Prompt engineering<br/>exercise_generation_v1]
    PR --> LLM[Transformer LLM<br/>local, via Ollama]
    LLM --> V{Validation<br/>schema · clinical · safety}
    V -- pass --> ISS[ExerciseIssuer + DB trigger]
    V -- fail --> RT[Retry] --> V2{Still failing?}
    V2 -- yes --> FB[Rule-based fallback] --> ISS
    V2 -- no --> ISS
    ISS --> E
```

Full GenAI write-up (ML, DL, NLP, transformer, prompts, examples):
[docs/review2-genai.md](docs/review2-genai.md).

## 🛡️ Clinical safety layers

```mermaid
flowchart LR
    L1[1. Progression rule<br/>clamped to range] --> L2[2. Generator<br/>picks only allowed pictures]
    L2 --> L3[3. ExerciseIssuer<br/>sole creator, validates]
    L3 --> L4[4. PostgreSQL trigger<br/>rejects out-of-range rows]
    L4 --> OK([Patient receives<br/>a safe exercise])
```

The runtime database role cannot alter tables, disable the trigger, or edit constraint
versions and audit logs.

---

## 🧰 Tech stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 16 (App Router) · TypeScript · Tailwind CSS 4 · Zod · Lucide |
| Backend | FastAPI · Pydantic v2 · SQLAlchemy 2 (async) · Alembic |
| Data | PostgreSQL 18 · Redis 8 · MinIO (S3-compatible) |
| Speech | faster-whisper `small.en` (CPU int8, self-hosted) |
| AI | Local transformer LLM (Qwen2.5 3B via Ollama) behind a provider interface · offline fake provider for tests |
| Ops | Docker Compose · Caddy · GitHub Actions |
| Testing | pytest · Hypothesis · Vitest · Playwright · axe-core |

## 🚀 Quick start

```bash
cp .env.example .env                       # fill in the change-me values
docker compose up -d --wait
cd backend
uv run python -m app.scripts.provision_storage
uv run alembic upgrade head && uv run python -m app.scripts.seed_dev
uv run uvicorn app.main:app --port 8000    # API
uv run python -m app.workers.main          # speech worker (second terminal)
cd ../frontend && npm install && npm run dev   # → http://localhost:3000
```

Real generative AI (local, $0): install [Ollama](https://ollama.com), run
`ollama pull qwen2.5:3b`, and set `AI_PROVIDER=ollama` in `.env` (optionally
`AI_DEMO_VIEW=true` for the clinician's step-by-step AI pipeline view).

Self-hosted HTTPS stack: `docker compose --env-file .env.production -f compose.prod.yaml up -d --build`
(see [deployment](docs/deployment.md)).

## ✅ Quality

- **146** backend tests, including property-based tests of the max-difficulty rule
- Frontend unit tests and **Playwright end-to-end** tests, with axe accessibility checks on every screen
- Phone and tablet layout checks, dependency audits, and a CI workflow

## 📚 Documentation

[Architecture](docs/architecture.md) ·
[Clinical constraints](docs/clinical-constraints.md) ·
[AI pipeline](docs/ai-pipeline.md) ·
[Clinician workflow](docs/clinician-workflow.md) ·
[Security](docs/security.md) ·
[Privacy](docs/privacy.md) ·
[Accessibility](docs/accessibility.md) ·
[Deployment](docs/deployment.md) ·
[Development](docs/development.md) ·
[Photo credits](docs/photo-credits.md)
