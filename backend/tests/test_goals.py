from app.users.models import Role
from tests.conftest import assign, create_user, patient_id
from tests.test_clinician_insights import base, run_session
from tests.test_practice import as_user, care, set_plan  # noqa: F401

MY_GOALS = "/api/v1/practice/goals"


async def test_goals_are_set_by_the_clinician_and_measured_from_practice(care):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(clinician, pid, allowed_exercise_types=["picture_naming"])
    url = f"{base(pid)}/goals"

    words = (await clinician.post(url, json={"kind": "name_words", "target": 1})).json()
    days = (await clinician.post(url, json={"kind": "practice_days", "target": 3})).json()
    assert words["title"] == "Name 1 word on your own" and words["progress"] == 0
    assert days["title"] == "Practise on 3 days this week"
    themed = (
        await clinician.post(url, json={"kind": "name_words", "target": 10, "category": "food"})
    ).json()
    assert themed["title"] == "Name 10 food words on your own"

    # Three active goals at most; invalid goals are refused.
    r = await clinician.post(url, json={"kind": "practice_days", "target": 2})
    assert r.status_code == 409
    assert (
        await clinician.post(url, json={"kind": "practice_days", "target": 8})
    ).status_code == 422
    r = await clinician.post(url, json={"kind": "name_words", "target": 5, "category": "planets"})
    assert r.status_code == 422

    # Progress comes from practice: the same word right three times is "on your own".
    for _ in range(4):
        await run_session(patient, [True] * 8)
    mine = {g["id"]: g for g in (await patient.get(MY_GOALS)).json()}
    assert mine[days["id"]]["progress"] == 1
    assert mine[words["id"]]["status"] == "achieved" and mine[words["id"]]["progress"] == 1

    # Ending a goal hides it from the patient but keeps it for the clinician.
    await clinician.post(f"{url}/{themed['id']}/end")
    assert themed["id"] not in {g["id"] for g in (await patient.get(MY_GOALS)).json()}
    listed = {g["id"]: g["status"] for g in (await clinician.get(url)).json()}
    assert listed[themed["id"]] == "ended"


async def test_goals_belong_to_the_care_team(care):  # noqa: F811
    patient, clinician, pid = care
    other = await create_user("cb@x.test", Role.CLINICIAN)
    pb = await create_user("pb@x.test", Role.PATIENT)
    await assign(pb, other)
    outsider = await as_user("cb@x.test")
    url = f"{base(pid)}/goals"
    assert (
        await outsider.post(url, json={"kind": "practice_days", "target": 3})
    ).status_code == 404
    assert (await patient.post(url, json={"kind": "practice_days", "target": 3})).status_code == 403
    assert (await clinician.get(MY_GOALS)).status_code == 403
    assert await patient_id(pb)
