import uuid

import pytest
from sqlalchemy import select, text, update
from sqlalchemy.exc import DBAPIError

from app.clinical.models import ConstraintSet
from app.core.db import SessionLocal
from app.exercises.generator import Proposal
from app.exercises.issuer import validate
from app.exercises.models import Exercise, Stimulus
from app.sessions.models import PracticeSession
from app.users.models import Role
from tests.conftest import assign, create_user, login, make_client, patient_id

START = "/api/v1/practice/sessions"


def plan(**overrides):
    return {
        "allowed_exercise_types": ["picture_naming"],
        "allowed_response_modes": ["text"],
        "min_difficulty": 1,
        "max_difficulty": 3,
        "max_exercises_per_session": 8,
        "advance_after_correct": 1,
        "step_back_after_incorrect": 1,
        **overrides,
    }


async def as_user(email):
    c = make_client()
    assert (await login(c, email)).status_code == 200
    return c


@pytest.fixture
async def care():
    """Patient + assigned clinician; returns (patient_client, clinician_client, patient_id)."""
    p = await create_user("p@x.test", Role.PATIENT)
    c = await create_user("c@x.test", Role.CLINICIAN)
    await assign(p, c)
    return await as_user("p@x.test"), await as_user("c@x.test"), await patient_id(p)


async def set_plan(clinician, pid, **overrides):
    r = await clinician.post(f"/api/v1/patients/{pid}/constraints", json=plan(**overrides))
    assert r.status_code == 201, r.text
    return r.json()


async def target_of(exercise_id: str) -> str:
    async with SessionLocal() as db:
        return (await db.get(Exercise, uuid.UUID(exercise_id))).expected["target"]


async def answer(client, state, *, correct: bool):
    ex = state["exercise"]
    text_ = await target_of(ex["id"]) if correct else "zzzz"
    r = await client.post(f"/api/v1/practice/exercises/{ex['id']}/responses", json={"text": text_})
    assert r.status_code == 200, r.text
    return r.json()


async def issued(pid: str) -> list[Exercise]:
    async with SessionLocal() as db:
        rows = await db.execute(select(Exercise).where(Exercise.patient_id == uuid.UUID(pid)))
        return list(rows.scalars())


# ---------- core loop ----------


async def test_no_plan_means_no_session(care):
    patient, _, _ = care
    assert (await patient.get("/api/v1/practice/status")).json()["has_plan"] is False
    assert (await patient.post(START)).status_code == 409


async def test_exercise_payload_never_reveals_the_answer(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid)
    r = await patient.post(START)
    ex = r.json()["exercise"]
    assert set(ex) == {
        "id",
        "position",
        "type",
        "prompt",
        "instructions",
        "image_url",
        "response_modes",
        "cues",
        "words",
        "image_kind",
    }
    target = await target_of(ex["id"])
    assert target not in r.text.replace(ex["image_url"], "")


async def test_full_session_flow(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid, max_exercises_per_session=3)
    state = (await patient.post(START)).json()
    assert state["exercise"]["position"] == 1

    # Resume returns the same pending exercise.
    assert (await patient.post(START)).json()["exercise"]["id"] == state["exercise"]["id"]

    r1 = await answer(patient, state, correct=True)
    assert r1["outcome"] == "correct" and r1["state"]["exercise"]["position"] == 2
    r2 = await answer(patient, r1["state"], correct=False)
    assert r2["outcome"] == "incorrect" and r2["target"]
    r3 = await answer(patient, r2["state"], correct=True)
    assert r3["state"]["status"] == "completed"
    assert r3["state"]["exercise"] is None
    assert r3["state"]["summary"] == {"practiced": 3, "correct": 2, "near_miss": 0}
    assert (await patient.get("/api/v1/practice/sessions/current")).status_code == 404


async def test_exercise_cannot_be_answered_twice(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid)
    state = (await patient.post(START)).json()
    await answer(patient, state, correct=True)
    r = await patient.post(
        f"/api/v1/practice/exercises/{state['exercise']['id']}/responses", json={"text": "x"}
    )
    assert r.status_code == 409


async def test_skip_and_end_session(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid)
    state = (await patient.post(START)).json()
    r = await patient.post(
        f"/api/v1/practice/exercises/{state['exercise']['id']}/responses", json={"skipped": True}
    )
    assert r.json()["outcome"] == "skipped"
    assert (await patient.post("/api/v1/practice/sessions/current/end")).status_code == 204
    assert (await patient.get("/api/v1/practice/status")).json()["has_active_session"] is False


async def test_patient_cannot_answer_another_patients_exercise(care):
    _, clinician, pid = care
    await set_plan(clinician, pid)
    owner = await as_user("p@x.test")
    state = (await owner.post(START)).json()
    await create_user("other@x.test", Role.PATIENT)
    other = await as_user("other@x.test")
    r = await other.post(
        f"/api/v1/practice/exercises/{state['exercise']['id']}/responses", json={"text": "x"}
    )
    assert r.status_code == 404


async def test_activity_counts_own_practice_only_and_never_scores(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid, max_exercises_per_session=2)
    state = (await patient.post(START)).json()
    r1 = await answer(patient, state, correct=True)
    await answer(patient, r1["state"], correct=False)

    body = (await patient.get("/api/v1/practice/activity")).json()
    assert body["sessions_completed"] == 1
    assert body["pictures_practised"] == 2
    assert [s["answered"] for s in body["recent"]] == [2]
    # Activity only: nothing about correctness reaches the patient's home page.
    assert "correct" not in str(body).replace("sessions_completed", "")

    await create_user("other@x.test", Role.PATIENT)
    other = (await (await as_user("other@x.test")).get("/api/v1/practice/activity")).json()
    assert other == {"sessions_completed": 0, "pictures_practised": 0, "recent": []}
    # Clinicians use their own views, not the patient endpoint.
    assert (await clinician.get("/api/v1/practice/activity")).status_code == 403


# ---------- clinical constraints: the critical invariant ----------


@pytest.mark.parametrize("max_d", [1, 2, 3, 4])
async def test_no_exercise_ever_exceeds_max_difficulty(care, max_d):
    """MAX_DIFFICULTY = N ⇒ no patient exercise has difficulty > N, even for a patient
    who answers everything correctly (progression pushes upward every answer)."""
    patient, clinician, pid = care
    await set_plan(clinician, pid, max_difficulty=max_d, max_exercises_per_session=10)
    for _ in range(2):
        state = (await patient.post(START)).json()
        while state["exercise"]:
            state = (await answer(patient, state, correct=True))["state"]
    difficulties = [e.difficulty for e in await issued(pid)]
    assert len(difficulties) == 20
    assert max(difficulties) == max_d  # progression reaches the ceiling…
    assert all(d <= max_d for d in difficulties)  # …and never passes it


async def test_never_below_min_difficulty(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid, min_difficulty=3, max_difficulty=4)
    state = (await patient.post(START)).json()
    while state["exercise"]:
        state = (await answer(patient, state, correct=False))["state"]
    assert {e.difficulty for e in await issued(pid)} == {3}


async def test_lowered_ceiling_applies_to_the_very_next_exercise(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid, min_difficulty=1, max_difficulty=5)
    state = (await patient.post(START)).json()
    for _ in range(4):
        state = (await answer(patient, state, correct=True))["state"]
    new = await set_plan(clinician, pid, max_difficulty=1)
    state = (await answer(patient, state, correct=True))["state"]
    async with SessionLocal() as db:
        nxt = await db.get(Exercise, uuid.UUID(state["exercise"]["id"]))
    assert nxt.difficulty == 1
    assert str(nxt.constraint_set_id) == new["id"]


async def test_allowed_categories_are_respected(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid, allowed_categories=["animals"], max_difficulty=5)
    state = (await patient.post(START)).json()
    while state["exercise"]:
        state = (await answer(patient, state, correct=True))["state"]
    async with SessionLocal() as db:
        cats = (
            await db.execute(
                select(Stimulus.category).join(Exercise, Exercise.stimulus_id == Stimulus.id)
            )
        ).scalars()
        assert set(cats) == {"animals"}


async def test_unimplemented_types_issue_nothing(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid, allowed_exercise_types=["sentence_completion"])
    assert (await patient.post(START)).status_code == 409
    assert await issued(pid) == []


async def test_speech_only_plan_issues_speech_only_exercises(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid, allowed_response_modes=["speech"])
    ex = (await patient.post(START)).json()["exercise"]
    assert ex["response_modes"] == ["speech"]
    r = await patient.post(f"/api/v1/practice/exercises/{ex['id']}/responses", json={"text": "x"})
    assert r.status_code == 409  # typed answers refused when the clinician allows speech only


async def test_issuer_rejects_out_of_range_proposal():
    cs = ConstraintSet(
        patient_id=uuid.uuid4(),
        allowed_exercise_types=["picture_naming"],
        allowed_response_modes=["text"],
        allowed_categories=None,
        min_difficulty=1,
        max_difficulty=3,
        max_exercises_per_session=8,
    )
    session = PracticeSession(patient_id=cs.patient_id, planned_exercises=8)
    stim = Stimulus(
        difficulty=4, category="tools", is_active=True, exercise_types=["picture_naming"]
    )
    p = Proposal("picture_naming", 4, ["speech"], stim, {}, {}, "ai")
    assert set(validate(p, cs, session, 9)) == {
        "difficulty_out_of_range",
        "response_mode_not_allowed",
        "session_limit_reached",
    }


# ---------- defence in depth: database ----------


async def test_db_trigger_blocks_out_of_range_exercise_even_without_the_issuer(care):
    patient, clinician, pid = care
    await set_plan(clinician, pid, max_difficulty=3)
    state = (await patient.post(START)).json()
    async with SessionLocal() as db:
        ex = await db.get(Exercise, uuid.UUID(state["exercise"]["id"]))
        with pytest.raises(DBAPIError, match="outside clinician range"):
            await db.execute(update(Exercise).where(Exercise.id == ex.id).values(difficulty=4))
        await db.rollback()


async def test_db_trigger_blocks_stale_constraint_version(care):
    patient, clinician, pid = care
    v1 = await set_plan(clinician, pid)
    state = (await patient.post(START)).json()
    await set_plan(clinician, pid)
    async with SessionLocal() as db:
        with pytest.raises(DBAPIError, match="latest constraint set"):
            await db.execute(
                update(Exercise)
                .where(Exercise.id == uuid.UUID(state["exercise"]["id"]))
                .values(constraint_set_id=uuid.UUID(v1["id"]))
            )
        await db.rollback()


async def test_constraint_versions_are_immutable(care):
    _, clinician, pid = care
    await set_plan(clinician, pid)
    async with SessionLocal() as db:
        with pytest.raises(DBAPIError):
            await db.execute(text("UPDATE clinical_constraint_sets SET max_difficulty = 5"))


# ---------- who may set constraints ----------


async def test_only_assigned_clinicians_set_constraints(care):
    patient, clinician, pid = care
    url = f"/api/v1/patients/{pid}/constraints"
    assert (await patient.post(url, json=plan())).status_code == 403
    await create_user("c2@x.test", Role.CLINICIAN)
    assert (await (await as_user("c2@x.test")).post(url, json=plan())).status_code == 404
    await create_user("a@x.test", Role.ADMIN)
    assert (await (await as_user("a@x.test")).post(url, json=plan())).status_code == 403
    assert (
        await clinician.post(url, json=plan(min_difficulty=4, max_difficulty=2))
    ).status_code == 422
    assert (await clinician.post(url, json=plan(max_difficulty=6))).status_code == 422
    assert (
        await clinician.post(url, json=plan(allowed_exercise_types=["diagnose"]))
    ).status_code == 422
    first = await set_plan(clinician, pid)
    second = await set_plan(clinician, pid)
    assert (first["version"], second["version"]) == (1, 2)
    assert (await clinician.get(url)).json()["version"] == 2
