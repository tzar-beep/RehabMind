from sqlalchemy import select

from app.core.db import SessionLocal
from app.users.models import Role, User
from tests.conftest import create_user, login, make_client
from tests.test_clinician_insights import base, run_session
from tests.test_practice import as_user, care, set_plan  # noqa: F401


async def _carer(admin, patient_email: str, email="carer@x.test", relationship="daughter"):
    async with SessionLocal() as db:
        patient_user = await db.scalar(select(User).where(User.email == patient_email))
    r = await admin.post(
        "/api/v1/admin/users",
        json={
            "email": email,
            "display_name": "Priya",
            "role": "carer",
            "patient_user_id": str(patient_user.id),
            "relationship": relationship,
        },
    )
    assert r.status_code == 201, r.text
    client = make_client()
    assert (await login(client, email, r.json()["initial_password"])).status_code == 200
    return client


async def test_a_carer_sees_activity_and_goals_but_no_clinical_data(care):  # noqa: F811
    patient, clinician, pid = care
    await create_user("admin@x.test", Role.ADMIN)
    admin = await as_user("admin@x.test")
    carer = await _carer(admin, "p@x.test")

    await set_plan(clinician, pid, max_exercises_per_session=2)
    await run_session(patient, [True, False])
    await clinician.post(f"{base(pid)}/goals", json={"kind": "practice_days", "target": 3})

    mine = (await carer.get("/api/v1/carer/patients")).json()
    assert mine == [{"id": pid, "display_name": "p", "relationship": "daughter"}]
    summary = (await carer.get(f"/api/v1/carer/patients/{pid}")).json()
    assert summary["activity"]["pictures_practised"] == 2
    assert summary["goals"][0]["title"] == "Practise on 3 days this week"
    # Counts only: nothing about right or wrong.
    assert "correct" not in str(summary)

    for path in ("/overview", "/sessions", "/words", "/goals"):
        assert (await carer.get(f"{base(pid)}{path}")).status_code == 403
    assert (await carer.get("/api/v1/practice/status")).status_code == 403

    users = {u["email"]: u for u in (await admin.get("/api/v1/admin/users")).json()}
    assert users["carer@x.test"]["supports"] == ["p (daughter)"]


async def test_carers_only_reach_the_patient_they_support(care):  # noqa: F811
    _, _, pid = care
    await create_user("admin@x.test", Role.ADMIN)
    await create_user("p2@x.test", Role.PATIENT)
    admin = await as_user("admin@x.test")
    carer = await _carer(admin, "p2@x.test")
    assert (await carer.get(f"/api/v1/carer/patients/{pid}")).status_code == 404

    # A carer must be linked to a patient, with how they know them.
    r = await admin.post(
        "/api/v1/admin/users",
        json={"email": "lone@x.test", "display_name": "Lone", "role": "carer"},
    )
    assert r.status_code == 422
