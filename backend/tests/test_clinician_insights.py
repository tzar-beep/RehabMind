import json

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from app.ai.provider import set_ai_provider
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.main import app
from app.users.models import Role, User
from app.workers.queue import get_job_queue
from tests.conftest import assign, create_user, patient_id
from tests.test_ai import ai  # noqa: F401
from tests.test_practice import START, answer, as_user, care, set_plan  # noqa: F401
from tests.test_speech import FakeProvider, InlineQueue, upload


async def run_session(patient, pattern: list[bool]) -> str:
    state = (await patient.post(START)).json()
    sid = state["session_id"]
    for correct in pattern:
        state = (await answer(patient, state, correct=correct))["state"]
    return sid


def base(pid: str) -> str:
    return f"/api/v1/patients/{pid}"


# ---------- dashboard ----------


async def test_dashboard_lists_only_assigned_patients_with_real_counts(care):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(clinician, pid, max_exercises_per_session=3)
    await run_session(patient, [True, True, False])

    # A second assigned patient with no activity, and one patient assigned to nobody.
    p2 = await create_user("p2@x.test", Role.PATIENT)
    await create_user("unassigned@x.test", Role.PATIENT)
    async with SessionLocal() as db:
        me = await db.scalar(select(User).where(User.email == "c@x.test"))
    await assign(p2, me)

    rows = (await clinician.get("/api/v1/clinicians/me/patients")).json()
    assert {r["display_name"] for r in rows} == {"p", "p2"}
    first = next(r for r in rows if r["id"] == pid)
    assert first["sessions_completed"] == 1
    assert (first["recent_responses"], first["recent_correct"]) == (3, 2)
    assert first["constraints"]["max_difficulty"] == 3
    second = next(r for r in rows if r["display_name"] == "p2")
    assert second["sessions_completed"] == 0 and second["last_session_at"] is None
    assert second["constraints"] is None and second["recent_responses"] == 0


# ---------- patient profile ----------


async def test_overview_reports_observed_activity(care):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(clinician, pid, max_exercises_per_session=3)
    await run_session(patient, [True, False, True])
    ov = (await clinician.get(f"{base(pid)}/overview")).json()
    assert ov["sessions_completed"] == 1 and ov["sessions_total"] == 1
    assert ov["outcomes"] == {"correct": 2, "near_miss": 0, "incorrect": 1, "skipped": 0}
    assert ov["by_mode"] == [{"mode": "text", "attempted": 3, "correct": 2}]
    assert ov["care_team"] == ["c"]
    assert 1 <= ov["current_working_difficulty"] <= 3
    assert ov["has_active_session"] is False


async def test_overview_empty_patient(care):  # noqa: F811
    _, clinician, pid = care
    ov = (await clinician.get(f"{base(pid)}/overview")).json()
    assert ov["sessions_total"] == 0 and ov["last_session_at"] is None
    assert ov["median_latency_ms"] is None and ov["current_working_difficulty"] is None
    assert (await clinician.get(f"{base(pid)}/trends")).json() == []


async def test_sessions_trends_and_detail(care):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(clinician, pid, max_exercises_per_session=2)
    s1 = await run_session(patient, [True, True])
    s2 = await run_session(patient, [False, True])

    page = (await clinician.get(f"{base(pid)}/sessions?limit=1")).json()
    assert page["total"] == 2 and [s["id"] for s in page["items"]] == [s2]
    page2 = (await clinician.get(f"{base(pid)}/sessions?limit=1&offset=1")).json()
    assert [s["id"] for s in page2["items"]] == [s1]
    assert page2["items"][0]["outcomes"]["correct"] == 2 and page2["items"][0]["modes"] == ["text"]
    assert page2["items"][0]["duration_s"] is not None

    trend = (await clinician.get(f"{base(pid)}/trends")).json()
    assert [t["session_id"] for t in trend] == [s1, s2]  # oldest first
    assert [t["accuracy"] for t in trend] == [1.0, 0.5]

    detail = (await clinician.get(f"{base(pid)}/sessions/{s2}")).json()
    assert [e["position"] for e in detail["exercises"]] == [1, 2]
    assert [e["outcome"] for e in detail["exercises"]] == ["incorrect", "correct"]
    assert detail["exercises"][0]["response_text"] == "zzzz"
    assert detail["exercises"][0]["target"] and detail["exercises"][0]["source"] in {
        "ai",
        "rule",
        "fallback",
    }


# ---------- constraint history ----------


async def test_constraint_history_is_versioned_and_read_only(care):  # noqa: F811
    _, clinician, pid = care
    await set_plan(clinician, pid, max_difficulty=2)
    await set_plan(clinician, pid, max_difficulty=4, note="Progressing")
    versions = (await clinician.get(f"{base(pid)}/constraints/versions")).json()
    assert [(v["version"], v["is_active"], v["max_difficulty"]) for v in versions] == [
        (2, True, 4),
        (1, False, 2),
    ]
    assert versions[0]["created_by"] == "c" and versions[0]["note"] == "Progressing"
    for method in ("put", "patch", "delete"):
        r = await getattr(clinician, method)(f"{base(pid)}/constraints")
        assert r.status_code == 405


# ---------- AI runs ----------


@pytest.mark.parametrize(
    ("plan", "result", "sources"),
    [
        ([None], "ai_generated", {"ai"}),
        (["answer_leak", None], "ai_generated_after_retry", {"ai"}),
        (["unsafe_text", "provider_error"], "rule_based_used", {"rule", "fallback"}),
    ],
)
async def test_ai_runs_explain_what_the_patient_received(care, ai, plan, result, sources):  # noqa: F811
    patient, clinician, pid = care
    ai(plan)
    await set_plan(clinician, pid)
    await patient.post(START)
    [run] = (await clinician.get(f"{base(pid)}/ai-generations/runs")).json()
    assert run["result"] == result and run["position"] == 1
    assert run["final_exercise"]["source"] in sources
    assert len(run["attempts"]) == len(plan)
    assert run["constraint_version"] == 1 and run["prompt_version"] == "picture-naming-v1"
    if result != "rule_based_used":
        assert run["selection_reason"] in {
            "reinforce_recent_error",
            "consolidate_success",
            "introduce_new",
            "category_variety",
        }
    else:
        assert run["selection_reason"] is None
        assert [a["failed_stage"] for a in run["attempts"]] == ["safety", "provider"]
    assert "reasoning" not in json.dumps(run) and "raw_output" not in run
    for method in ("post", "put", "delete"):
        r = await getattr(clinician, method)(f"{base(pid)}/ai-generations/runs")
        assert r.status_code == 405


# ---------- isolation ----------

ROUTES = [
    "/overview",
    "/trends",
    "/sessions",
    "/constraints",
    "/constraints/versions",
    "/ai-generations",
    "/ai-generations/runs",
]


async def test_clinicians_only_see_their_own_patients(care):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(clinician, pid)
    sid = await run_session(patient, [True])

    # A second care team: clinician B with their own patient B.
    pb = await create_user("pb@x.test", Role.PATIENT)
    cb = await create_user("cb@x.test", Role.CLINICIAN)
    await assign(pb, cb)
    pid_b = await patient_id(pb)
    clinician_b = await as_user("cb@x.test")

    for route in ROUTES:
        assert (await clinician_b.get(base(pid) + route)).status_code == 404, route
        assert (await clinician.get(base(pid) + route)).status_code in {200}, route
    # Session of patient A addressed through clinician B's own patient: still 404.
    assert (await clinician_b.get(f"{base(pid_b)}/sessions/{sid}")).status_code == 404
    assert (await clinician_b.get(f"{base(pid)}/sessions/{sid}")).status_code == 404
    assert (await clinician_b.post(f"{base(pid)}/constraints", json={})).status_code in {404, 422}
    assert [p["id"] for p in (await clinician_b.get("/api/v1/clinicians/me/patients")).json()] == [
        pid_b
    ]


@pytest.mark.parametrize("role", [Role.PATIENT, Role.ADMIN])
async def test_non_clinicians_cannot_use_clinician_views(care, role):  # noqa: F811
    patient, _, pid = care
    if role is Role.ADMIN:
        await create_user("adm@x.test", Role.ADMIN)
        patient = await as_user("adm@x.test")
    for route in ROUTES:
        assert (await patient.get(base(pid) + route)).status_code == 403, route


# ---------- privacy ----------


async def test_session_detail_never_exposes_audio(care):  # noqa: F811
    patient, clinician, pid = care
    provider = FakeProvider()
    app.dependency_overrides[get_job_queue] = lambda: InlineQueue(provider)
    set_ai_provider(None)
    try:
        await set_plan(clinician, pid, allowed_response_modes=["text", "speech"])
        state = (await patient.post(START)).json()
        provider.text, provider.no_speech_prob = "", 0.95
        await upload(patient, state["exercise"]["id"])  # unclear → retry
        provider.text, provider.no_speech_prob = "zzzz", 0.01
        await upload(patient, state["exercise"]["id"])
    finally:
        app.dependency_overrides.pop(get_job_queue, None)

    detail = (await clinician.get(f"{base(pid)}/sessions/{state['session_id']}")).json()
    first = detail["exercises"][0]
    assert first["response_mode"] == "speech" and first["response_text"] == "zzzz"
    assert [a["status"] for a in first["speech_attempts"]] == ["no_speech", "done"]
    assert first["transcript_quality"]["no_speech_prob"] == 0.01
    blob = json.dumps(detail).lower()
    assert "object_key" not in blob and "audio/" not in blob and "audio_url" not in blob


async def test_constraint_options_come_from_backend_rules(care):  # noqa: F811
    patient, clinician, _ = care
    opts = (await clinician.get("/api/v1/clinical/constraint-options")).json()
    types = {t["value"]: t["available"] for t in opts["exercise_types"]}
    assert types["picture_naming"] is True and types["sentence_completion"] is False
    assert opts["response_modes"] == ["text", "speech"]
    assert opts["difficulty"] == [1, 5] and "animals" in opts["categories"]
    assert (await patient.get("/api/v1/clinical/constraint-options")).status_code == 403


async def test_ai_runs_group_rows_recorded_before_slot_tracking(care, ai):  # noqa: F811
    """Rows without exercise_position (pre-migration) are grouped by transaction."""
    patient, clinician, pid = care
    ai(["answer_leak", None])
    await set_plan(clinician, pid)
    await patient.post(START)
    # Simulate legacy rows (the schema owner may update; the runtime role may not).
    engine = create_async_engine(get_settings().migration_database_url)
    async with engine.begin() as conn:
        await conn.execute(text("UPDATE ai_generations SET exercise_position = NULL"))
    await engine.dispose()

    [run] = (await clinician.get(f"{base(pid)}/ai-generations/runs")).json()
    assert run["result"] == "ai_generated_after_retry"
    assert len(run["attempts"]) == 2 and run["position"] == 1
    assert run["final_exercise"]["source"] == "ai"
