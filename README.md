# RehabMind

**AI-assisted, clinician-bounded speech and language practice for people recovering from
stroke-related aphasia.**

Patients name pictures by speaking or typing. RehabMind transcribes speech on its own
server, scores each answer, and personalizes the next exercise, always inside limits set by
the patient's clinician. Clinicians see real practice data, manage those limits as versioned
settings, and can audit every AI decision.

> Academic / research prototype. Not a diagnostic tool, not clinically validated, and not
> an autonomous system: the clinician is always the authority.

---

## Highlights

**For patients**
- One picture, one question, one big button: designed to reduce cognitive load
- Answer by **voice or typing**, with progressive hints (meaning first, then first sound)
- Warm, honest feedback that always shows the picture with the correct word
- Accessible: WCAG 2.1 AA target, large targets, legible typography, reduced motion

**For clinicians**
- Dashboard of assigned patients with factual activity, and nothing invented
- Accuracy and difficulty trends, session history, transcript confidence
- **Versioned practice limits**: each change creates a new immutable version
- **AI audit log**: what the AI suggested, which check rejected it, and what the patient got

**Safety by design**
- `MAX_DIFFICULTY = 3` ⇒ never difficulty 4: enforced by the progression rule, the
  generator, a single exercise issuer **and** a database trigger
- Generative AI is a bounded component, not an agent: every output passes format,
  clinical and safety validation, with retry and a deterministic fallback
- Patient audio is **encrypted, transcribed locally, then deleted**; Whisper
  hallucinations are never scored
- Strict data isolation: clinicians only ever see their own patients

**$0 to run**: no paid APIs and no keys. Speech recognition (faster-whisper) and AI
personalization run locally.

## Architecture

```
Browser ─HTTPS─▶ Caddy ─▶ Next.js (UI) ─▶ FastAPI ─▶ PostgreSQL · Redis · MinIO
                                          ARQ worker ─▶ faster-whisper · AI provider
```

Modular monolith + background worker. Next.js 16, TypeScript, Tailwind · FastAPI,
SQLAlchemy 2, Alembic · PostgreSQL 18 · Redis 8 · MinIO · faster-whisper.

## Quick start (local development)

```bash
cp .env.example .env                       # then fill in the change-me values
docker compose up -d --wait
cd backend && uv run python -m app.scripts.provision_storage
uv run alembic upgrade head && uv run python -m app.scripts.seed_dev
uv run uvicorn app.main:app --port 8000    # API
uv run python -m app.workers.main          # speech worker (another terminal)
cd ../frontend && npm install && npm run dev   # http://localhost:3000
```

Self-hosted production-like stack: see [docs/deployment.md](docs/deployment.md).

## Quality

150+ backend tests, frontend unit tests, Playwright end-to-end tests with axe
accessibility checks, dependency audits and CI.

## Documentation

[Architecture](docs/architecture.md) ·
[Development](docs/development.md) ·
[Clinical constraints](docs/clinical-constraints.md) ·
[AI pipeline](docs/ai-pipeline.md) ·
[Clinician workflow](docs/clinician-workflow.md) ·
[Security](docs/security.md) ·
[Privacy](docs/privacy.md) ·
[Accessibility](docs/accessibility.md) ·
[Deployment](docs/deployment.md)
