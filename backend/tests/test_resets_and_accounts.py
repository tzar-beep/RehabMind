import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.core.db import SessionLocal
from app.sessions.models import PracticeSession, ProgressReset
from app.users.models import Role, User
from tests.conftest import assign, create_user, login, make_client, patient_id
from tests.test_practice import START, answer, as_user, set_plan

RESET = "/api/v1/patients/{}/progress-resets"
USERS = "/api/v1/admin/users"


@pytest.fixture
async def care():
    p = await create_user("p@x.test", Role.PATIENT)
    c = await create_user("c@x.test", Role.CLINICIAN)
    await assign(p, c)
    return await as_user("p@x.test"), await as_user("c@x.test"), await patient_id(p)


# ---------- progress reset ----------


async def test_reset_gives_a_fresh_start_without_deleting_anything(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid, max_exercises_per_session=2, advance_after_correct=1)
    state = (await patient.post(START)).json()
    r1 = await answer(patient, state, correct=True)
    await answer(patient, r1["state"], correct=True)
    # Leave a session open so the reset must close it.
    assert (await patient.post(START)).json()["status"] == "active"
    before = (await clinician.get(f"/api/v1/patients/{pid}/overview")).json()
    assert before["sessions_completed"] == 1 and before["current_working_difficulty"] > 1

    r = await clinician.post(RESET.format(pid), json={"reason": "Starting a new therapy block"})
    assert r.status_code == 201, r.text
    assert r.json()["by"] and r.json()["reason"] == "Starting a new therapy block"

    ov = (await clinician.get(f"/api/v1/patients/{pid}/overview")).json()
    assert ov["sessions_total"] == 0 and ov["outcomes"]["correct"] == 0
    assert ov["current_working_difficulty"] is None
    assert ov["last_reset"]["reason"] == "Starting a new therapy block"
    assert (await clinician.get(f"/api/v1/patients/{pid}/trends")).json() == []
    activity = (await patient.get("/api/v1/practice/activity")).json()
    assert activity == {"sessions_completed": 0, "pictures_practised": 0, "recent": []}
    listed = (await clinician.get("/api/v1/clinicians/me/patients")).json()[0]
    assert listed["sessions_completed"] == 0 and listed["recent_responses"] == 0

    # History is kept and labelled, not deleted.
    page = (await clinician.get(f"/api/v1/patients/{pid}/sessions")).json()
    assert page["total"] == 2 and all(s["before_reset"] for s in page["items"])
    async with SessionLocal() as db:
        statuses = (
            await db.scalars(
                select(PracticeSession.status).where(PracticeSession.patient_id == uuid.UUID(pid))
            )
        ).all()
    assert sorted(statuses) == ["completed", "ended"]

    # The next session starts again at the clinician's minimum difficulty and counts.
    fresh = (await patient.post(START)).json()
    assert fresh["status"] == "active" and fresh["exercise"]["position"] == 1
    await answer(patient, fresh, correct=False)
    ov = (await clinician.get(f"/api/v1/patients/{pid}/overview")).json()
    assert ov["sessions_total"] == 1 and ov["outcomes"]["incorrect"] == 1
    assert ov["current_working_difficulty"] == 1


async def test_only_assigned_clinicians_can_reset(care):
    patient, _, pid = care
    await create_user("c2@x.test", Role.CLINICIAN)
    await create_user("a@x.test", Role.ADMIN)
    body = {"reason": "test reason"}
    assert (await patient.post(RESET.format(pid), json=body)).status_code == 403
    admin = await as_user("a@x.test")
    assert (await admin.post(RESET.format(pid), json=body)).status_code == 403
    other = await as_user("c2@x.test")
    assert (await other.post(RESET.format(pid), json=body)).status_code == 404


async def test_reset_requires_a_reason(care):
    _, clinician, pid = care
    assert (await clinician.post(RESET.format(pid), json={"reason": " "})).status_code == 422
    assert (await clinician.post(RESET.format(pid), json={})).status_code == 422


async def test_resets_are_append_only_for_the_runtime_role(care):
    _, clinician, pid = care
    await clinician.post(RESET.format(pid), json={"reason": "test reason"})
    async with SessionLocal() as db:
        assert await db.scalar(select(ProgressReset.id))
        with pytest.raises(DBAPIError):
            await db.execute(text("DELETE FROM progress_resets"))
        await db.rollback()
        with pytest.raises(DBAPIError):
            await db.execute(text("UPDATE progress_resets SET reason = 'x'"))


# ---------- admin: add users ----------


@pytest.fixture
async def admin():
    await create_user("a@x.test", Role.ADMIN)
    return await as_user("a@x.test")


async def test_admin_creates_patient_assigned_to_clinician(admin):
    c = await create_user("c@x.test", Role.CLINICIAN)
    r = await admin.post(
        USERS,
        json={
            "email": "New.Patient@X.test",
            "display_name": "Jo",
            "role": "patient",
            "clinician_user_id": str(c.id),
        },
    )
    assert r.status_code == 201, r.text
    body = r.json()
    password = body["initial_password"]
    assert len(password) == 19 and password.count("-") == 3
    assert body["user"]["email"] == "new.patient@x.test"

    # The password works, is stored only as a hash, and the clinician now sees the patient.
    assert (await login(make_client(), "new.patient@x.test", password)).status_code == 200
    async with SessionLocal() as db:
        stored = await db.scalar(
            select(User.password_hash).where(User.email == "new.patient@x.test")
        )
    assert password not in stored and stored.startswith("$argon2id$")
    clinician = await as_user("c@x.test")
    patients = (await clinician.get("/api/v1/clinicians/me/patients")).json()
    assert [p["display_name"] for p in patients] == ["Jo"]


async def test_admin_creates_clinician_and_passwords_differ(admin):
    a = await admin.post(
        USERS, json={"email": "d1@x.test", "display_name": "Dr A", "role": "clinician"}
    )
    b = await admin.post(
        USERS, json={"email": "d2@x.test", "display_name": "Dr B", "role": "clinician"}
    )
    assert a.status_code == b.status_code == 201
    assert a.json()["initial_password"] != b.json()["initial_password"]


async def test_create_user_rejects_bad_input(admin):
    p = await create_user("p@x.test", Role.PATIENT)
    dup = {"email": "p@x.test", "display_name": "Dup", "role": "patient"}
    assert (await admin.post(USERS, json=dup)).status_code == 409
    bad_email = {"email": "not-an-email", "display_name": "X", "role": "patient"}
    assert (await admin.post(USERS, json=bad_email)).status_code == 422
    # Assigning to someone who is not a clinician is refused.
    wrong = {
        "email": "q@x.test",
        "display_name": "Q",
        "role": "patient",
        "clinician_user_id": str(p.id),
    }
    assert (await admin.post(USERS, json=wrong)).status_code == 422


async def test_only_admins_create_users(admin):
    await create_user("c@x.test", Role.CLINICIAN)
    await create_user("p@x.test", Role.PATIENT)
    body = {"email": "z@x.test", "display_name": "Z", "role": "admin"}
    for email in ("c@x.test", "p@x.test"):
        assert (await (await as_user(email)).post(USERS, json=body)).status_code == 403


async def test_admin_assigns_a_clinician_to_an_unassigned_patient(admin):
    p = await create_user("p@x.test", Role.PATIENT)
    c = await create_user("c@x.test", Role.CLINICIAN)
    users = {u["email"]: u for u in (await admin.get(USERS)).json()}
    assert users["p@x.test"]["care_team"] == []
    url = f"{USERS}/{p.id}/care-team"
    r = await admin.post(url, json={"clinician_user_id": str(c.id)})
    assert r.status_code == 200 and r.json()["care_team"] == [c.display_name]
    assert (await admin.post(url, json={"clinician_user_id": str(c.id)})).status_code == 200
    clinician = await as_user("c@x.test")
    assert len((await clinician.get("/api/v1/clinicians/me/patients")).json()) == 1
    # Only patients have a care team; only clinicians can join one.
    bad = await admin.post(f"{USERS}/{c.id}/care-team", json={"clinician_user_id": str(c.id)})
    assert bad.status_code == 409
    wrong = await admin.post(url, json={"clinician_user_id": str(p.id)})
    assert wrong.status_code == 422


async def test_admin_resets_a_password_and_old_sessions_end(admin):
    p = await create_user("p@x.test", Role.PATIENT)
    patient = await as_user("p@x.test")
    assert (await patient.get("/api/v1/auth/me")).status_code == 200
    r = await admin.post(f"{USERS}/{p.id}/password")
    assert r.status_code == 200
    new_password = r.json()["initial_password"]
    assert (await patient.get("/api/v1/auth/me")).status_code == 401  # signed out everywhere
    assert (await login(make_client(), "p@x.test")).status_code == 401  # old password gone
    assert (await login(make_client(), "p@x.test", new_password)).status_code == 200


async def test_admin_disables_and_enables_an_account(admin):
    p = await create_user("p@x.test", Role.PATIENT)
    patient = await as_user("p@x.test")
    url = f"{USERS}/{p.id}/active"
    r = await admin.put(url, json={"active": False})
    assert r.status_code == 200 and r.json()["is_active"] is False
    assert (await patient.get("/api/v1/auth/me")).status_code == 401
    assert (await login(make_client(), "p@x.test")).status_code == 401
    assert (await admin.put(url, json={"active": True})).json()["is_active"] is True
    assert (await login(make_client(), "p@x.test")).status_code == 200


async def test_admin_cannot_disable_themselves_and_others_cannot_manage(admin):
    me = (await admin.get("/api/v1/auth/me")).json()
    assert (
        await admin.put(f"{USERS}/{me['id']}/active", json={"active": False})
    ).status_code == 409
    p = await create_user("p@x.test", Role.PATIENT)
    await create_user("c@x.test", Role.CLINICIAN)
    clinician = await as_user("c@x.test")
    assert (await clinician.post(f"{USERS}/{p.id}/password")).status_code == 403
    assert (
        await clinician.put(f"{USERS}/{p.id}/active", json={"active": False})
    ).status_code == 403
