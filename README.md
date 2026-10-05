# Stroke Recovery AI

Personalized aphasia rehabilitation platform. Patients practise language exercises;
generative AI personalizes the next exercise **within clinician-defined constraints**;
clinicians review progress, AI output and validation history.

Not a diagnostic tool and not an autonomous system. The clinician is the authority.

## Stack

Next.js · TypeScript · Tailwind — FastAPI · SQLAlchemy 2 · Alembic — PostgreSQL ·
Redis (sessions, ARQ jobs) · S3-compatible storage (MinIO locally) · faster-whisper · OpenAI (via provider abstraction)

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

## Status

Phase 1 complete: authentication, RBAC, patient isolation, audit, design system foundation.
