import json
import uuid

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import DBAPIError

from app.ai.fake import FAULTS, FakeAIProvider
from app.ai.models import AIGeneration
from app.ai.provider import GenerationRequest, set_ai_provider
from app.ai.schemas import PROMPT_VERSION, PictureNamingOutput
from app.clinical.models import ConstraintSet
from app.core.db import SessionLocal
from app.exercises.models import Exercise, Stimulus
from app.users.models import Role
from app.validation.exercise import check_clinical, check_safety, check_schema
from tests.conftest import create_user
from tests.test_practice import START, answer, as_user, care, issued, set_plan  # noqa: F401


@pytest.fixture
def ai():
    """Install a FakeAIProvider with an explicit fault plan for one test."""

    def install(plan: list[str | None] | None = None, fault_rate: float = 0.0) -> FakeAIProvider:
        provider = FakeAIProvider(fault_rate=fault_rate, fault_plan=plan)
        set_ai_provider(provider)
        return provider

    yield install
    set_ai_provider(None)  # next get_ai_provider() rebuilds from settings


async def generations(pid: str) -> list[AIGeneration]:
    async with SessionLocal() as db:
        rows = await db.execute(
            select(AIGeneration)
            .where(AIGeneration.patient_id == uuid.UUID(pid))
            .order_by(AIGeneration.created_at, AIGeneration.attempt)
        )
        return list(rows.scalars())


# ---------- validation stages (pure) ----------

CUP = Stimulus(
    slug="cup",
    target="cup",
    accepted_answers=["cup", "mug"],
    category="food",
    difficulty=2,
    exercise_types=["picture_naming"],
    is_active=True,
)
CS = ConstraintSet(
    min_difficulty=1,
    max_difficulty=3,
    allowed_categories=None,
    allowed_exercise_types=["picture_naming"],
    allowed_response_modes=["text"],
)


def out(**kw) -> PictureNamingOutput:
    base = {
        "stimulus_slug": "cup",
        "difficulty": 2,
        "prompt": "What is this?",
        "semantic_cue": "It's something you can eat or drink.",
        "phonemic_cue": "c",
        "rationale": "category_variety",
    }
    return PictureNamingOutput.model_validate({**base, **kw})


@pytest.mark.parametrize(
    ("raw", "code"),
    [
        ('{"stimulus_slug": "cup"', "invalid_json"),
        ("[1, 2]", "not_an_object"),
        (json.dumps({"stimulus_slug": "cup"}), "missing:difficulty"),
        (
            json.dumps({**out().model_dump(mode="json"), "reasoning": "..."}),
            "extra_forbidden:reasoning",
        ),
        (json.dumps({**out().model_dump(mode="json"), "rationale": "because"}), "enum:rationale"),
        (
            json.dumps({**out().model_dump(mode="json"), "difficulty": 9}),
            "less_than_equal:difficulty",
        ),
    ],
)
def test_schema_stage_rejects(raw, code):
    v = check_schema(raw)
    assert not v.ok and v.stage == "schema" and code in v.reasons


def test_schema_stage_accepts_valid_output():
    assert check_schema(json.dumps(out().model_dump(mode="json"))).ok


@pytest.mark.parametrize(
    ("kw", "code"),
    [
        ({"stimulus_slug": "stethoscope"}, "stimulus_not_in_candidates"),
        ({"difficulty": 4}, "difficulty_out_of_range"),
        ({"difficulty": 1}, "difficulty_mismatch"),
    ],
)
def test_clinical_stage_rejects(kw, code):
    v = check_clinical(out(**kw), CS, {"cup": CUP})
    assert not v.ok and v.stage == "clinical" and code in v.reasons


def test_clinical_stage_enforces_categories():
    cs = ConstraintSet(min_difficulty=1, max_difficulty=3, allowed_categories=["animals"])
    assert "category_not_allowed" in check_clinical(out(), cs, {"cup": CUP}).reasons


@pytest.mark.parametrize(
    ("kw", "code"),
    [
        ({"prompt": "Is this a cup?"}, "answer_leak:prompt"),
        ({"prompt": "Name these mugs"}, "answer_leak:prompt"),
        ({"semantic_cue": "This will help your brain heal."}, "medical_claim:semantic_cue"),
        ({"semantic_cue": "Your aphasia is improving."}, "medical_claim:semantic_cue"),
        ({"semantic_cue": "You should have got this one"}, "pressure_language:semantic_cue"),
        ({"semantic_cue": "See www.example.org for more"}, "link_or_contact:semantic_cue"),
        ({"prompt": "What is this thing that you see here now?"}, "too_long:prompt"),
        ({"phonemic_cue": "b"}, "invalid_phonemic_cue"),
        ({"phonemic_cue": "cup"}, "invalid_phonemic_cue"),
    ],
)
def test_safety_stage_rejects(kw, code):
    v = check_safety(out(**kw), CUP)
    assert not v.ok and v.stage == "safety" and code in v.reasons


def test_safety_stage_accepts_plain_respectful_text():
    assert check_safety(out(), CUP).ok


# ---------- fake provider ----------


async def test_fake_provider_is_deterministic_and_offline():
    inp = {
        "candidates": [
            {"slug": "cup", "target": "cup", "category": "food", "difficulty": 2, "seen": False}
        ],
        "recent_outcomes": [],
        "category_accuracy": {},
        "category_counts": {},
        "max_difficulty": 3,
    }
    req = GenerationRequest("t", "v1", "s", "u", inp, {})
    a = await FakeAIProvider().generate(req)
    b = await FakeAIProvider().generate(req)
    assert a.raw_output == b.raw_output
    assert check_schema(a.raw_output).ok


# ---------- pipeline: generate → validate → accept / retry / fallback → audit ----------


async def test_valid_ai_output_is_issued_and_audited(care, ai):  # noqa: F811
    patient, clinician, pid = care
    ai([None])
    await set_plan(clinician, pid)
    ex = (await patient.post(START)).json()["exercise"]
    assert len(ex["cues"]) == 2 and ex["cues"][1].startswith("It starts with")

    [gen] = await generations(pid)
    assert gen.status == "accepted" and str(gen.exercise_id) == ex["id"]
    assert gen.provider == "fake" and gen.prompt_version == PROMPT_VERSION
    assert gen.constraint_version == 1 and gen.parsed_output["rationale"]
    async with SessionLocal() as db:
        assert (await db.get(Exercise, uuid.UUID(ex["id"]))).source == "ai"


@pytest.mark.parametrize("fault", [f for f in FAULTS if f != "provider_error"])
async def test_rejected_output_is_retried_then_accepted(care, ai, fault):  # noqa: F811
    patient, clinician, pid = care
    ai([fault, None])
    await set_plan(clinician, pid, max_difficulty=3)
    ex = (await patient.post(START)).json()["exercise"]
    first, second = await generations(pid)
    assert (first.attempt, first.status, first.exercise_id) == (1, "rejected", None)
    assert first.failed_stage in {"schema", "clinical", "safety"} and first.reason_codes
    assert (second.attempt, second.status, str(second.exercise_id)) == (2, "accepted", ex["id"])


async def test_repeated_failure_falls_back_to_deterministic_exercise(care, ai):  # noqa: F811
    patient, clinician, pid = care
    ai(["unsafe_text", "provider_error"])
    await set_plan(clinician, pid)
    ex = (await patient.post(START)).json()["exercise"]
    assert ex is not None  # the patient is never blocked by AI failure
    gens = await generations(pid)
    assert [(g.status, g.failed_stage) for g in gens] == [
        ("rejected", "safety"),
        ("error", "provider"),
    ]
    async with SessionLocal() as db:
        assert (await db.get(Exercise, uuid.UUID(ex["id"]))).source in {"rule", "fallback"}


async def test_ai_disabled_uses_rules_only(care, ai):  # noqa: F811
    patient, clinician, pid = care
    set_ai_provider(None)
    from app.core.config import get_settings

    get_settings().ai_provider = "none"
    try:
        await set_plan(clinician, pid)
        ex = (await patient.post(START)).json()["exercise"]
        assert ex and await generations(pid) == []
    finally:
        get_settings().ai_provider = "fake"


class AlwaysTooHard(FakeAIProvider):
    """A misbehaving model that always proposes the hardest picture in the library."""

    async def generate(self, request):
        result = await super().generate(request)
        data = json.loads(result.raw_output)
        data.update(stimulus_slug="microscope", difficulty=5)
        return result.__class__(json.dumps(data), result.provider, result.model)


async def test_max_difficulty_holds_against_a_hostile_model(care):  # noqa: F811
    """MAX_DIFFICULTY = 3 ⇒ no exercise above 3, even if the model always proposes 5."""
    patient, clinician, pid = care
    set_ai_provider(AlwaysTooHard())
    try:
        await set_plan(clinician, pid, max_difficulty=3, max_exercises_per_session=10)
        state = (await patient.post(START)).json()
        while state["exercise"]:
            state = (await answer(patient, state, correct=True))["state"]
        assert all(e.difficulty <= 3 for e in await issued(pid))
        gens = await generations(pid)
        assert gens and all(g.status == "rejected" for g in gens)
        assert all(g.failed_stage == "clinical" for g in gens)
    finally:
        set_ai_provider(None)


async def test_seeded_faults_never_break_the_invariant(care, ai):  # noqa: F811
    patient, clinician, pid = care
    ai(fault_rate=0.6)
    await set_plan(clinician, pid, max_difficulty=2, max_exercises_per_session=12)
    state = (await patient.post(START)).json()
    while state["exercise"]:
        state = (await answer(patient, state, correct=True))["state"]
    assert len(await issued(pid)) == 12
    assert all(e.difficulty <= 2 for e in await issued(pid))
    statuses = {g.status for g in await generations(pid)}
    assert {"accepted", "rejected"} <= statuses | {"error"}


async def test_ai_input_is_minimized(care, ai):  # noqa: F811
    patient, clinician, pid = care
    ai([None])
    await set_plan(clinician, pid)
    await patient.post(START)
    [gen] = await generations(pid)
    snapshot = json.dumps(gen.input_snapshot)
    assert pid not in snapshot and "p@x.test" not in snapshot and '"p"' not in snapshot
    assert set(gen.input_snapshot) == {
        "exercise_type",
        "target_difficulty",
        "min_difficulty",
        "max_difficulty",
        "recent_outcomes",
        "category_accuracy",
        "category_counts",
        "candidates",
    }


async def test_hints_hold_the_level(care, ai):  # noqa: F811
    patient, clinician, pid = care
    ai(fault_rate=0.0)
    await set_plan(clinician, pid, min_difficulty=1, max_difficulty=5, advance_after_correct=1)
    state = (await patient.post(START)).json()
    for _ in range(3):
        ex = state["exercise"]
        async with SessionLocal() as db:
            target = (await db.get(Exercise, uuid.UUID(ex["id"]))).expected["target"]
        r = await patient.post(
            f"/api/v1/practice/exercises/{ex['id']}/responses",
            json={"text": target, "hints_used": 2},
        )
        assert r.json()["outcome"] == "correct"
        state = r.json()["state"]
    assert {e.difficulty for e in await issued(pid)} == {1}


# ---------- audit trail access ----------


async def test_ai_audit_is_append_only(care, ai):  # noqa: F811
    patient, clinician, pid = care
    ai([None])
    await set_plan(clinician, pid)
    await patient.post(START)
    async with SessionLocal() as db:
        for sql in ("UPDATE ai_generations SET status = 'accepted'", "DELETE FROM ai_generations"):
            with pytest.raises(DBAPIError):
                await db.execute(text(sql))
            await db.rollback()


async def test_only_assigned_clinicians_read_ai_metadata(care, ai):  # noqa: F811
    patient, clinician, pid = care
    ai(["answer_leak", None])
    await set_plan(clinician, pid)
    await patient.post(START)
    url = f"/api/v1/patients/{pid}/ai-generations"
    rows = (await clinician.get(url)).json()
    assert [r["status"] for r in rows] == ["accepted", "rejected"]
    assert rows[1]["failed_stage"] == "safety" and rows[1]["reason_codes"] == ["answer_leak:prompt"]
    assert "raw_output" not in rows[0] and "reasoning" not in json.dumps(rows)
    assert (await patient.get(url)).status_code == 403
    await create_user("c2@x.test", Role.CLINICIAN)
    assert (await (await as_user("c2@x.test")).get(url)).status_code == 404
