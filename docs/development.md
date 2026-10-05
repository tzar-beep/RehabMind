# Development

## Prerequisites

- Docker Desktop (WSL 2 backend)
- Node.js 24 LTS (`.nvmrc`)
- Python 3.12 + [uv](https://docs.astral.sh/uv/)

## First run

```bash
cp .env.example .env          # then replace every change-me value
docker compose up -d --wait   # PostgreSQL :5433, Redis :6379, MinIO :9000 (127.0.0.1 only)
uv run scripts/bootstrap_storage.py
```

## Local infrastructure

| Service | Host port | Notes |
|---|---|---|
| PostgreSQL 18 | 5433 | 5432 avoided to coexist with a native Windows install. DBs: `stroke_recovery`, `stroke_recovery_test` |
| Redis 8 | 6379 | Password required |
| MinIO | 9000 | S3 API only (no console). Bucket `ephemeral-audio`: private, unversioned, 1-day expiry |

Database roles are created on first volume init by `docker/postgres/initdb/`:
`sra_migrator` (migrations) and `sra_app` (runtime, DML only).
To re-run init scripts, reset the volume: `docker compose down -v` (destroys local data).

## Rules

- Synthetic data only. Never use real patient recordings or records.
- Never commit `.env`, keys, audio, or patient data (`.gitignore` blocks common audio formats).
- Branch per feature (`feature/<name>`), focused commits, merge to `main`.

## Windows notes

- If `docker` is not found in an already-open terminal after installing Docker Desktop,
  restart the terminal (the installer updates the user PATH).
- The repository currently lives under OneDrive. Pause syncing or exclude `node_modules`,
  `.venv` and `.next` if file-lock errors appear; moving the repo outside OneDrive is preferred.
