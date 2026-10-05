# CLAUDE.md

Aphasia rehabilitation platform. Read `docs/architecture.md` before structural changes.

## Non-negotiables

- **No agentic AI.** No agents, planning loops, autonomous tool use, agent memory or
  orchestration frameworks. AI calls are single, bounded, schema-validated requests.
- **Clinician constraints > AI generation.** Exercises reach patients only through the
  server-side `ExerciseIssuer`; never bypass it. Frontend validation is never safety.
- **Never diagnose, prescribe, or claim standardized clinical scores** (WAB, BDAE, …).
- **No chain-of-thought** requested or stored. Audit with structured reason codes.
- **AI data minimization:** pseudonymous IDs and minimum context only.
- **Audio is ephemeral:** encrypt, process, delete. Never log, commit or expose it.
- **Authorization server-side**, every endpoint; patients see only their own data;
  admin does not imply clinical access.
- Never commit secrets, `.env`, real patient data or recordings. Dev seed accounts must
  never load outside `APP_ENV=development`.

## Conventions

- Backend: `uv`, FastAPI, Pydantic v2, SQLAlchemy 2 async, Alembic. Runtime DB role `rehabmind_app`
  is DML-only; migrations run as `rehabmind_migrator`.
- Frontend: Next.js App Router, TypeScript strict, Tailwind with design tokens, Zod.
- Accessibility: WCAG 2.1 AA; patient UI = one task, one question, one primary action; 48px targets.
- English only in V1; keep user-facing strings out of business logic.
- Branch per feature; focused commits.

## Commands

```bash
docker compose up -d --wait
(cd backend && uv run python -m app.scripts.provision_storage)
cd backend && uv run pytest && uv run ruff check .
cd backend && uv run python -m app.workers.main   # speech worker
cd frontend && npm run typecheck && npm run lint && npm test && npm run test:e2e
```

Patient data access goes through `backend/app/patients/access.py` only.
Frontend uses Next.js 16 — read `frontend/node_modules/next/dist/docs/` before using unfamiliar APIs.

## Working style

Concise. Plan briefly, implement, report: implemented / files / tests / blockers.
Ask only for decisions affecting clinical safety, security, privacy, architecture, cost,
data integrity or external services.
