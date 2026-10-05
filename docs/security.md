# Security

## Authentication

- **Server-side sessions.** Login issues a 256-bit random token in an `HttpOnly`,
  `SameSite=Lax` cookie (`Secure` + `__Host-` prefix in production). Redis stores the
  session under `SHA-256(token)`; the browser never holds anything readable by JS.
- **Expiry:** 30 min idle, 12 h absolute. Checked in code on every request, mirrored by Redis TTL.
- **Revocation:** logout (one session), logout-all (every device). Deactivated users or
  role changes invalidate sessions on the next request.
- **Session fixation:** any presented session is revoked at login; a fresh token is issued.
- **Passwords:** Argon2id, transparent rehash on parameter change. Unknown accounts are
  verified against a dummy hash so timing does not reveal account existence; error text is identical.
- **Rate limiting:** 5 failures per account and 30 attempts per IP per 15 min → HTTP 429.

## CSRF and origin

All API traffic is same-origin (Next.js rewrites `/api/*`). Unsafe methods require an
`Origin` (or `Referer`) in `FRONTEND_ORIGINS`; otherwise 403. Combined with `SameSite=Lax`.
CORS lists explicit origins only — never `*` with credentials (enforced at startup in production).

## Authorization

- Role dependencies (`PatientUser`, `ClinicianUser`, `AdminUser`) on every endpoint.
- Patient data is reachable **only** via `app/patients/access.py::accessible_patients`, which
  encodes the rule in SQL: patient → self; clinician → assigned patients; admin → none.
- Inaccessible records return 404 (indistinguishable from missing) and are audited as `denied`.
- Frontend role gates are navigation only; the backend is the authority.

## Database

| Role | Rights |
|---|---|
| `postgres` | Container admin only; never used by the app |
| `rehabmind_migrator` | Owns schema; runs Alembic |
| `rehabmind_app` | Runtime: DML only; cannot create/alter tables or disable triggers; INSERT/SELECT only on `audit_logs` |

## Audit

`audit_logs` is append-only for the runtime role. Records action, outcome, actor, target and
request ID. Never stores passwords, tokens, emails or clinical content in `details`.

## Logging and errors

JSON logs with request IDs; sensitive keys redacted; uvicorn access log disabled (paths/cookies).
Unhandled errors return a generic message. Responses carry `no-store`, `nosniff`,
`X-Frame-Options: DENY`, `Referrer-Policy: same-origin`.

## Secrets

`.env` is git-ignored; `.env.example` holds placeholders only. Settings fail fast when a
required secret is missing. Dev seed refuses to run unless `APP_ENV=development` on a local DB.

## Known gaps (Phase 6)

- Health check uses MinIO root credentials → scoped storage credentials.
- Content-Security-Policy header.
- Secrets manager for production; TLS termination and HSTS at the edge.
- Login rate limit by IP relies on `X-Forwarded-For` from the trusted Next.js proxy.
