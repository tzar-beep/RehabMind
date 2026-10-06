import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.db import SessionLocal
from app.users.models import Role
from tests.conftest import assign, create_user, login, make_client, patient_id


@pytest.fixture
async def world():
    p1 = await create_user("p1@x.test", Role.PATIENT)
    p2 = await create_user("p2@x.test", Role.PATIENT)
    c1 = await create_user("c1@x.test", Role.CLINICIAN)
    await create_user("c2@x.test", Role.CLINICIAN)
    await create_user("admin@x.test", Role.ADMIN)
    await assign(p1, c1)
    return {"p1": await patient_id(p1), "p2": await patient_id(p2)}


async def as_user(email):
    c = make_client()
    assert (await login(c, email)).status_code == 200
    return c


async def test_patient_reads_only_own_record(world):
    c = await as_user("p1@x.test")
    assert (await c.get("/api/v1/patients/me")).json()["id"] == world["p1"]
    assert (await c.get(f"/api/v1/patients/{world['p1']}")).status_code == 200
    assert (await c.get(f"/api/v1/patients/{world['p2']}")).status_code == 404


async def test_clinician_reads_only_assigned_patients(world):
    c1 = await as_user("c1@x.test")
    assert (await c1.get(f"/api/v1/patients/{world['p1']}")).status_code == 200
    assert (await c1.get(f"/api/v1/patients/{world['p2']}")).status_code == 404
    listed = (await c1.get("/api/v1/clinicians/me/patients")).json()
    assert [p["id"] for p in listed] == [world["p1"]]

    c2 = await as_user("c2@x.test")
    assert (await c2.get(f"/api/v1/patients/{world['p1']}")).status_code == 404
    assert (await c2.get("/api/v1/clinicians/me/patients")).json() == []


async def test_admin_has_no_implicit_clinical_access(world):
    a = await as_user("admin@x.test")
    assert (await a.get(f"/api/v1/patients/{world['p1']}")).status_code == 404
    assert (await a.get("/api/v1/clinicians/me/patients")).status_code == 403
    assert (await a.get("/api/v1/patients/me")).status_code == 403
    users = (await a.get("/api/v1/admin/users")).json()
    assert len(users) == 5
    # Account administration only. `care_team` (assigned clinicians' names) is needed to
    # manage assignments; no practice, limits, scores or AI data reach the admin.
    assert set(users[0]) == {"id", "email", "role", "display_name", "is_active", "care_team"}


@pytest.mark.parametrize(
    ("email", "path"),
    [
        ("p1@x.test", "/api/v1/admin/users"),
        ("p1@x.test", "/api/v1/clinicians/me/patients"),
        ("c1@x.test", "/api/v1/admin/users"),
        ("c1@x.test", "/api/v1/patients/me"),
    ],
)
async def test_role_boundaries(world, email, path):
    assert (await (await as_user(email)).get(path)).status_code == 403


async def test_denied_patient_access_is_audited(world):
    c = await as_user("p1@x.test")
    await c.get(f"/api/v1/patients/{world['p2']}")
    async with SessionLocal() as db:
        row = (
            await db.execute(
                text("SELECT action, target_id FROM audit_logs WHERE outcome = 'denied'")
            )
        ).one()
    assert tuple(row) == ("patient.read", world["p2"])


@pytest.mark.parametrize(
    "sql",
    [
        "UPDATE audit_logs SET outcome = 'success'",
        "DELETE FROM audit_logs",
        "ALTER TABLE users DISABLE TRIGGER ALL",
        "CREATE TABLE sneaky (id int)",
    ],
)
async def test_runtime_db_role_cannot_tamper(sql):
    async with SessionLocal() as db:
        with pytest.raises(DBAPIError):
            await db.execute(text(sql))
