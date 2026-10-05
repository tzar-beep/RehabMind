import logging

import pytest
from pydantic import SecretStr, ValidationError

from app.core.config import Settings, get_settings
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


def _prod(**overrides):
    strong = SecretStr("x" * 32)
    base = get_settings().model_dump()
    base.update(
        app_env="production",
        frontend_origins=["https://rehabmind.example"],
        postgres_app_password=strong,
        postgres_migrator_password=strong,
        redis_password=strong,
        s3_secret_key=strong,
        audio_encryption_key=strong,
        ai_fake_fault_rate=0,
        seed_dev_password=None,
    )
    base.update(overrides)
    return Settings.model_validate(base)


def test_production_settings_accept_strong_configuration():
    assert _prod().is_production


@pytest.mark.parametrize(
    ("override", "message"),
    [
        ({"redis_password": SecretStr("change-me-redis")}, "REDIS_PASSWORD"),
        ({"s3_secret_key": SecretStr("short")}, "S3_SECRET_KEY"),
        ({"ai_fake_fault_rate": 0.2}, "AI_FAKE_FAULT_RATE"),
        ({"seed_dev_password": SecretStr("x" * 20)}, "SEED_DEV_PASSWORD"),
        ({"frontend_origins": ["http://rehabmind.example"]}, "https"),
    ],
)
def test_production_refuses_unsafe_configuration(override, message):
    with pytest.raises(ValidationError, match=message):
        _prod(**override)


async def test_access_log_has_route_templates_not_ids(client, caplog):
    caplog.set_level(logging.INFO, logger="app.access")
    pid = "11111111-1111-1111-1111-111111111111"
    await client.get(f"/api/v1/patients/{pid}?secret=1")
    [record] = [r for r in caplog.records if r.name == "app.access"]
    assert record.data["route"] == "/api/v1/patients/{patient_id}"
    assert pid not in str(record.data) and "secret" not in str(record.data)
