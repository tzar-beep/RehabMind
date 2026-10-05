# Deployment (self-hosted, $0)

RehabMind runs as a single Docker Compose stack. No paid services, no API keys: speech
recognition and the AI provider run locally. Academic prototype — not certified for
clinical use.

```bash
python scripts/generate_prod_env.py                      # once; writes .env.production
docker compose --env-file .env.production -f compose.prod.yaml up -d --build
# create accounts (password prompted; never passed as an argument)
docker compose --env-file .env.production -f compose.prod.yaml exec api \
  python -m app.scripts.create_user --email dr@example.org --name "Dr. A" --role clinician
docker compose --env-file .env.production -f compose.prod.yaml exec api \
  python -m app.scripts.create_user --email pat@example.org --name "Sam" --role patient \
  --assign-to dr@example.org
```

Open `https://localhost` (Caddy's local CA: accept the certificate warning, or trust the CA).
The clinician sets practice limits in the UI before the patient can practise.

## Topology

```
browser ──HTTPS──▶ caddy (only published ports: 80→443, 443)
                     └─▶ web (Next.js standalone, :3000)
                           └─▶ api (FastAPI, :8000)  ─▶ postgres, redis, minio
                         worker (ARQ + faster-whisper) ─▶ postgres, redis, minio
one-shot: migrate (Alembic as schema owner + picture library sync)
          storage-init (bucket, lifecycle, least-privilege app user; only holder of root keys)
```

| Concern | How |
|---|---|
| TLS | Caddy; `tls internal` for localhost. For a real domain set `SITE_ADDRESS` and remove `tls internal` (automatic certificate). HSTS set. |
| Secrets | `.env.production` (git-ignored, generated). Each service receives only the variables it needs; settings refuse placeholder or short secrets in production. |
| Least privilege | DB runtime role DML-only; storage app user limited to `ephemeral-audio/audio/*`; containers run as non-root (uid 10001 / node `app`). |
| Exposure | API, DB, Redis, MinIO publish no ports; only Caddy does. API docs disabled in production. |
| Dev data | `seed_dev` refuses outside `APP_ENV=development`. |
| First start | The worker downloads Whisper `small.en` (~480 MB) once into the `whisper-models` volume. |
| Backups | `postgres-data` volume holds all records; MinIO holds only transient audio (no backup needed). Use `pg_dump` as the `postgres` user for backups. |

Verified locally: HTTPS, CSP/HSTS headers, `__Host-` Secure cookie, clinician → limits →
patient practice, real speech answer transcribed and audio deleted, API not reachable
directly, cross-care-team access denied.

## Not covered (would be needed for real clinical deployment)

Managed key service for `AUDIO_ENCRYPTION_KEY`, encrypted volumes/backups, centralised log
retention, uptime monitoring and alerting, a data-processing agreement and clinical safety
case, penetration testing, and user/account management in the UI (CLI only here).
