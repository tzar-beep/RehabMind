# Development

## Prerequisites

- Docker Desktop (WSL 2 backend)
- Node.js 24 LTS (`.nvmrc`)
- Python 3.12 + [uv](https://docs.astral.sh/uv/)

## First run

```bash
cp .env.example .env          # then replace every change-me value
docker compose up -d --wait   # PostgreSQL :5433, Redis :6379, MinIO :9000 (127.0.0.1 only)
(cd backend && uv run python -m app.scripts.provision_storage)
cd backend && uv run alembic upgrade head && uv run python -m app.scripts.seed_dev && cd ..
cd frontend && npm install && npm run copy-stimuli && cd ..
```

## Running

```bash
cd backend && uv run fastapi dev app/main.py     # API on :8000 (docs: /api/docs)
cd backend && uv run python -m app.workers.main  # speech worker (loads Whisper small.en)
cd frontend && npm run dev                       # UI on :3000, proxies /api to :8000
```

The seed also syncs the picture library and gives the dev patient a default plan
(picture naming, difficulty 1–3, 8 per session).

Dev accounts: `patient@`, `clinician@`, `admin@recovery.local`; password is `SEED_DEV_PASSWORD` in `.env`.

## Tests

```bash
cd backend && uv run pytest            # uses rehabmind_test DB + Redis DB 15
cd backend && uv run ruff check .
cd frontend && npm run typecheck && npm run lint && npm test
cd frontend && npx playwright install chromium && npm run test:e2e   # starts API, worker, UI
# Real-speech e2e: set E2E_FAKE_AUDIO to a synthetic speech .wav (default fake mic = tone)
```

## Local infrastructure

| Service | Host port | Notes |
|---|---|---|
| PostgreSQL 18 | 5433 | 5432 avoided to coexist with a native Windows install. DBs: `rehabmind`, `rehabmind_test` |
| Redis 8 | 6379 | Password required |
| MinIO | 9000 | S3 API only (no console). Bucket `ephemeral-audio`: private, unversioned, 1-day expiry |

Database roles are created on first volume init by `docker/postgres/initdb/`:
`rehabmind_migrator` (migrations) and `rehabmind_app` (runtime, DML only).
To re-run init scripts, reset the volume: `docker compose down -v` (destroys local data).

## Rules

- Synthetic data only. Never use real patient recordings or records.
- Never commit `.env`, keys, audio, or patient data (`.gitignore` blocks common audio formats).
- Branch per feature (`feature/<name>`), focused commits, merge to `main`.

## Windows notes

- The repository is under OneDrive, which does not support hard links: if `uv` fails with
  "incompatible hardlinks", set `UV_LINK_MODE=copy`.
- Local services use `127.0.0.1`, not `localhost`: Windows resolves `localhost` to IPv6 first,
  Docker publishes IPv4 only, and the fallback costs ~1 s per connection.
- First worker start downloads the Whisper `small.en` model (~480 MB) to the Hugging Face cache.

- If `docker` is not found in an already-open terminal after installing Docker Desktop,
  restart the terminal (the installer updates the user PATH).
- The repository currently lives under OneDrive. Pause syncing or exclude `node_modules`,
  `.venv` and `.next` if file-lock errors appear; moving the repo outside OneDrive is preferred.
