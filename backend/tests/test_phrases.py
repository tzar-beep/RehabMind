from tests.test_clinician_insights import base
from tests.test_practice import care  # noqa: F401

URL = "/api/v1/practice/phrases"


async def test_patient_practises_scripts_and_the_clinician_sees_how_often(care):  # noqa: F811
    patient, clinician, pid = care
    scripts = {s["id"]: s for s in (await patient.get(URL)).json()}
    assert scripts["cafe"]["lines"][0] == "Hello."
    assert "My name is p." in scripts["meeting"]["lines"]  # the patient's own name
    assert scripts["cafe"]["times_practised"] == 0

    assert (await patient.post(f"{URL}/cafe/done", json={"lines_said": 4})).status_code == 201
    assert (await patient.post(f"{URL}/cafe/done", json={"lines_said": 99})).status_code == 422
    assert (await patient.post(f"{URL}/nope/done", json={"lines_said": 1})).status_code == 404
    assert {s["id"]: s for s in (await patient.get(URL)).json()}["cafe"]["times_practised"] == 1

    summary = {s["id"]: s for s in (await clinician.get(f"{base(pid)}/phrases")).json()}
    assert summary["cafe"]["times_recent"] == 1 and summary["cafe"]["lines_said_share"] == 0.8
    assert summary["phone"]["times_total"] == 0 and summary["phone"]["lines_said_share"] is None
    assert (await clinician.post(f"{URL}/cafe/done", json={"lines_said": 1})).status_code == 403
