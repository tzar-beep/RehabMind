# RehabMind

Personalized aphasia rehabilitation platform. Patients practise language exercises;
generative AI personalizes the next exercise **within clinician-defined constraints**;
clinicians review progress, AI output and validation history.

Academic/research prototype. Not a diagnostic tool, not clinically validated, and not an autonomous system. The clinician is the authority.

## Stack

Next.js · TypeScript · Tailwind — FastAPI · SQLAlchemy 2 · Alembic — PostgreSQL ·
Redis (sessions, ARQ jobs) · S3-compatible storage (MinIO locally) · faster-whisper · pluggable AI provider (offline fake by default, no paid APIs)

## Quick start

See [docs/development.md](docs/development.md).

```bash
cp .env.example .env
docker compose up -d --wait
uv run scripts/bootstrap_storage.py
```

## Documentation

- [Architecture](docs/architecture.md)
- [Development](docs/development.md)
- [Security](docs/security.md)
- [Clinical constraints & practice loop](docs/clinical-constraints.md)
- [Privacy & audio lifecycle](docs/privacy.md)
- [AI pipeline](docs/ai-pipeline.md)
- [Clinician workflow](docs/clinician-workflow.md)

## Status

Phase 5 complete: clinician platform (dashboard, patient profile, sessions, versioned practice limits, AI audit log). Academic prototype; not clinically validated.
