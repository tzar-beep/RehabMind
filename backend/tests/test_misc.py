import pytest

from app.core.config import get_settings
from app.core.logging import _redact
from app.scripts.seed_dev import assert_seed_allowed


@pytest.mark.parametrize(
    ("env", "host"),
    [("production", "localhost"), ("test", "localhost"), ("development", "db.prod.internal")],
)
def test_dev_seed_refuses_outside_local_development(env, host):
    s = get_settings().model_copy(update={"app_env": env, "postgres_host": host})
    with pytest.raises(RuntimeError):
        assert_seed_allowed(s)


def test_dev_seed_allowed_locally():
    assert_seed_allowed(get_settings().model_copy(update={"app_env": "development"}))


def test_log_redaction():
    out = _redact({"password": "x", "nested": {"session_token": "y", "ok": 1}})
    assert out == {"password": "[redacted]", "nested": {"session_token": "[redacted]", "ok": 1}}


async def test_health(client):
    assert (await client.get("/api/health/live")).json() == {"status": "ok"}
    r = await client.get("/api/health/ready")
    assert r.status_code == 200, r.json()


async def test_security_headers(client):
    r = await client.get("/api/health/live")
    assert r.headers["x-content-type-options"] == "nosniff"
    assert r.headers["cache-control"] == "no-store"
