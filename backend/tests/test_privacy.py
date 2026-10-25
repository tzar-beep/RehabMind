import json

from app.users.models import Role
from tests.conftest import create_user
from tests.test_carers import _carer
from tests.test_clinician_insights import run_session
from tests.test_practice import as_user, care, set_plan  # noqa: F401

URL = "/api/v1/practice/my-information"


async def test_patient_sees_who_can_see_and_can_stop_sharing(care):  # noqa: F811
    patient, clinician, pid = care
    await create_user("admin@x.test", Role.ADMIN)
    carer = await _carer(await as_user("admin@x.test"), "p@x.test")
    info = (await patient.get(URL)).json()
    assert info["care_team"] == ["c"]
    assert [(f["name"], f["relationship"]) for f in info["family"]] == [("Priya", "daughter")]

    r = await patient.delete(f"{URL}/family/{info['family'][0]['user_id']}")
    assert r.status_code == 204
    assert (await patient.get(URL)).json()["family"] == []
    assert (await carer.get(f"/api/v1/carer/patients/{pid}")).status_code == 404
    assert (await clinician.get(URL)).status_code == 403


async def test_patient_downloads_their_information(care):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(clinician, pid, max_exercises_per_session=2)
    await run_session(patient, [True, False])
    r = await patient.get(f"{URL}/export")
    assert r.status_code == 200 and "attachment" in r.headers["content-disposition"]
    data = json.loads(r.text)
    assert len(data["answers"]) == 2 and data["answers"][0]["result"] == "correct"
    assert data["name"] == "p" and "recordings are never kept" in data["about"]
