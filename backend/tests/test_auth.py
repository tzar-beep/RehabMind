from sqlalchemy import select

from app.audit.models import AuditLog
from app.auth import sessions
from app.core.db import SessionLocal
from app.users.models import Role, User
from tests.conftest import PASSWORD, create_user, login, make_client

ME = "/api/v1/auth/me"


async def test_login_sets_httponly_session_cookie(client):
    await create_user("p@x.test", Role.PATIENT)
    r = await login(client, "P@X.test")
    assert r.status_code == 200
    assert r.json()["role"] == "patient"
    cookie = r.headers["set-cookie"].lower()
    assert "httponly" in cookie and "samesite=lax" in cookie
    assert (await client.get(ME)).status_code == 200


async def test_invalid_password_and_unknown_email_are_indistinguishable(client):
    await create_user("p@x.test", Role.PATIENT)
    bad_pw = await login(client, "p@x.test", "wrong-password")
    unknown = await login(client, "nobody@x.test")
    assert bad_pw.status_code == unknown.status_code == 401
    assert bad_pw.json() == unknown.json()
    assert (await client.get(ME)).status_code == 401


async def test_inactive_user_cannot_login(client):
    await create_user("p@x.test", Role.PATIENT, active=False)
    assert (await login(client, "p@x.test")).status_code == 401


async def test_unauthenticated_and_forged_sessions_rejected(client):
    assert (await client.get(ME)).status_code == 401
    client.cookies.set("sra_session", "forged-token")
    assert (await client.get(ME)).status_code == 401


async def test_logout_revokes_session_server_side(client):
    await create_user("p@x.test", Role.PATIENT)
    await login(client, "p@x.test")
    token = client.cookies["sra_session"]
    assert (await client.post("/api/v1/auth/logout")).status_code == 204
    replay = make_client()
    replay.cookies.set("sra_session", token)
    assert (await replay.get(ME)).status_code == 401


async def test_logout_all_revokes_every_device():
    await create_user("p@x.test", Role.PATIENT)
    a, b = make_client(), make_client()
    await login(a, "p@x.test")
    await login(b, "p@x.test")
    assert (await a.post("/api/v1/auth/logout-all")).status_code == 204
    assert (await b.get(ME)).status_code == 401


async def test_relogin_discards_previous_session(client):
    await create_user("p@x.test", Role.PATIENT)
    await login(client, "p@x.test")
    old = client.cookies["sra_session"]
    await login(client, "p@x.test")
    replay = make_client()
    replay.cookies.set("sra_session", old)
    assert (await replay.get(ME)).status_code == 401


async def test_idle_timeout_expires_session(client, monkeypatch):
    await create_user("p@x.test", Role.PATIENT)
    t = [1_000_000.0]
    monkeypatch.setattr(sessions, "now", lambda: t[0])
    await login(client, "p@x.test")
    t[0] += 29 * 60
    assert (await client.get(ME)).status_code == 200  # activity refreshes the idle timer
    t[0] += 29 * 60
    assert (await client.get(ME)).status_code == 200
    t[0] += 31 * 60
    assert (await client.get(ME)).status_code == 401


async def test_absolute_timeout_expires_active_session(client, monkeypatch):
    await create_user("p@x.test", Role.PATIENT)
    t = [1_000_000.0]
    monkeypatch.setattr(sessions, "now", lambda: t[0])
    await login(client, "p@x.test")
    codes = []
    for _ in range(26):  # active every 29 min for > 12 h
        t[0] += 29 * 60
        codes.append((await client.get(ME)).status_code)
    assert codes[0] == 200 and codes[-1] == 401


async def test_deactivated_user_loses_existing_session(client):
    user = await create_user("p@x.test", Role.PATIENT)
    await login(client, "p@x.test")
    async with SessionLocal() as db:
        (await db.get(User, user.id)).is_active = False
        await db.commit()
    assert (await client.get(ME)).status_code == 401


async def test_account_lockout_after_repeated_failures(client):
    await create_user("p@x.test", Role.PATIENT)
    for _ in range(5):
        assert (await login(client, "p@x.test", "wrong")).status_code == 401
    assert (await login(client, "p@x.test", PASSWORD)).status_code == 429


async def test_unsafe_requests_require_allowed_origin():
    await create_user("p@x.test", Role.PATIENT)
    assert (await login(make_client(origin=None), "p@x.test")).status_code == 403
    assert (await login(make_client(origin="https://evil.example"), "p@x.test")).status_code == 403


async def test_login_events_are_audited_without_secrets(client):
    await create_user("p@x.test", Role.PATIENT)
    await login(client, "p@x.test", "wrong")
    await login(client, "p@x.test")
    async with SessionLocal() as db:
        rows = (await db.execute(select(AuditLog).order_by(AuditLog.id))).scalars().all()
    assert [(r.action, r.outcome) for r in rows] == [
        ("auth.login", "failure"),
        ("auth.login", "success"),
    ]
    assert not any(PASSWORD in str(r.details) or "p@x.test" in str(r.details) for r in rows)
