import json
import re
import uuid
from pathlib import Path

import pytest
from sqlalchemy import select

from app.ai.fake import FakeAIProvider
from app.ai.provider import set_ai_provider
from app.analysis.scoring import score_description, score_sentence
from app.core.db import SessionLocal
from app.exercises.catalog import load_catalog
from app.exercises.generator import scrambled
from app.exercises.models import Exercise, Stimulus
from app.main import app
from app.workers.queue import get_job_queue
from tests.test_ai import ai, generations  # noqa: F401
from tests.test_practice import START, care, issued, set_plan  # noqa: F401
from tests.test_speech import FakeProvider, InlineQueue, upload

PUBLIC = Path(__file__).resolve().parents[2] / "frontend" / "public"
# Rotation order = ExerciseType order.
PHOTO_TYPES = ["picture_naming", "sentence_construction", "picture_description"]
OPEN_LICENSE = re.compile(r"^(CC0|Public domain|CC BY(-SA)? [0-9.]+( us)?)$")


# ---------- catalogue integrity ----------


def test_photo_catalogue_loads_with_required_metadata():
    photos = load_catalog()["photos"]
    assert 50 <= len(photos) <= 100
    required = {
        "slug",
        "image_path",
        "category",
        "difficulty",
        "exercise_types",
        "target",
        "accepted_answers",
        "source",
        "license",
        "attribution",
        "source_url",
    }
    for p in photos:
        assert required <= set(p), p["slug"]
        assert p["image_path"].startswith("/stimuli/photos/") and p["image_path"].endswith(".jpg")
        assert OPEN_LICENSE.match(p["license"]), (p["slug"], p["license"])
        assert p["source_url"].startswith("https://commons.wikimedia.org/wiki/File:")
        assert 1 <= p["difficulty"] <= 5 and set(p["exercise_types"]) <= set(PHOTO_TYPES)
    assert len({p["slug"] for p in photos}) == len(photos)


def test_every_referenced_image_exists_locally():
    catalog = load_catalog()
    paths = [p["image_path"] for p in catalog["photos"]]
    paths += [f"/stimuli/{s['slug']}.svg" for s in catalog["stimuli"]]
    missing = [p for p in paths if not (PUBLIC / p.lstrip("/")).is_file()]
    assert missing == []


def test_scene_photos_have_scoring_content():
    for p in load_catalog()["photos"]:
        if "picture_description" in p["exercise_types"]:
            concepts = p["description"]["concepts"]
            assert len(concepts) >= 2 and all(c["terms"] for c in concepts)
            # The model sentence itself must earn full marks.
            assert score_description(p["target"], concepts).outcome == "correct", p["slug"]
        if "sentence_construction" in p["exercise_types"]:
            words = p["sentence"]["words"]
            assert score_sentence(" ".join(words), p["target"], p["accepted_answers"]).outcome == (
                "correct"
            ), p["slug"]
            assert scrambled(words) != words  # the word bank never shows the answer order


async def test_photos_are_synced_into_the_stimulus_table():
    async with SessionLocal() as db:
        photos = (
            (await db.execute(select(Stimulus).where(Stimulus.kind == "photo"))).scalars().all()
        )
    assert len(photos) == len(load_catalog()["photos"])
    assert all(p.is_active and p.license and p.source_url for p in photos)


# ---------- scoring ----------

CYCLING = [
    {"name": "person", "terms": ["person", "man", "someone"]},
    {"name": "bicycle", "terms": ["bicycle", "bike"]},
    {"name": "riding", "terms": ["riding", "ride", "cycling"]},
    {"name": "road", "terms": ["road", "street"], "optional": True},
]


@pytest.mark.parametrize(
    ("answer", "outcome", "matched"),
    [
        ("Someone is riding a bicycle.", "correct", ["person", "bicycle", "riding"]),
        ("a MAN on a bike", "near_miss", ["person", "bicycle"]),
        ("bike", "incorrect", ["bicycle"]),
        ("a man riding a bike on the road", "correct", ["person", "bicycle", "riding", "road"]),
        ("a dog", "incorrect", []),
        ("", "skipped", []),
    ],
)
def test_picture_description_scoring(answer, outcome, matched):
    r = score_description(answer, CYCLING)
    assert (r.outcome, r.details["concepts_matched"]) == (outcome, matched)


@pytest.mark.parametrize(
    ("answer", "outcome"),
    [
        ("The dog is running.", "correct"),
        ("  the   DOG is running ", "correct"),
        ("A dog is running", "correct"),
        ("dog the is running", "near_miss"),
        ("the cat is running", "incorrect"),
        ("I don't know", "skipped"),
    ],
)
def test_sentence_construction_scoring(answer, outcome):
    r = score_sentence(answer, "The dog is running.", ["a dog is running"])
    assert r.outcome == outcome


# ---------- selection respects clinician limits ----------


async def _exercises(pid: str) -> list[tuple[Exercise, Stimulus]]:
    async with SessionLocal() as db:
        rows = await db.execute(
            select(Exercise, Stimulus)
            .join(Stimulus, Stimulus.id == Exercise.stimulus_id)
            .where(Exercise.patient_id == uuid.UUID(pid))
            .order_by(Exercise.position)
        )
        return list(rows.all())


async def _answer_all(patient, state, text="zzzz"):
    while state["exercise"]:
        ex = state["exercise"]
        if ex["type"] == "sentence_construction":
            text = " ".join(ex["words"])
        r = await patient.post(
            f"/api/v1/practice/exercises/{ex['id']}/responses", json={"text": text}
        )
        assert r.status_code == 200, r.text
        state = r.json()["state"]
    return state


@pytest.mark.parametrize("exercise_type", ["picture_description", "sentence_construction"])
async def test_new_types_use_photos_within_limits(care, exercise_type):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(
        clinician,
        pid,
        allowed_exercise_types=[exercise_type],
        allowed_categories=["animals"],
        min_difficulty=1,
        max_difficulty=2,
        max_exercises_per_session=4,
    )
    state = (await patient.post(START)).json()
    assert state["exercise"]["type"] == exercise_type
    assert state["exercise"]["image_kind"] == "photo"
    await _answer_all(patient, state)
    rows = await _exercises(pid)
    assert len(rows) == 4
    for ex, stim in rows:
        assert ex.exercise_type == exercise_type and stim.kind == "photo"
        assert stim.category == "animals" and ex.difficulty <= 2
        assert exercise_type in stim.exercise_types


async def test_mixed_plan_rotates_types_and_prefers_photos(care):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(
        clinician,
        pid,
        allowed_exercise_types=PHOTO_TYPES,
        min_difficulty=1,
        max_difficulty=3,
        max_exercises_per_session=6,
    )
    await _answer_all(patient, (await patient.post(START)).json())
    rows = await _exercises(pid)
    assert [ex.exercise_type for ex, _ in rows] == PHOTO_TYPES * 2
    assert all(stim.kind == "photo" for _, stim in rows)
    assert max(ex.difficulty for ex, _ in rows) <= 3


async def test_line_drawings_remain_available_as_fallback(care):  # noqa: F811
    """No photo at difficulty 5 for naming → the Lucide drawings are still used."""
    patient, clinician, pid = care
    await set_plan(clinician, pid, min_difficulty=5, max_difficulty=5, max_exercises_per_session=2)
    state = (await patient.post(START)).json()
    assert state["exercise"]["type"] == "picture_naming"
    assert state["exercise"]["image_kind"] == "icon"


async def test_new_exercises_do_not_reveal_answers(care):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(clinician, pid, allowed_exercise_types=PHOTO_TYPES[1:])
    r = await patient.post(START)
    ex = r.json()["exercise"]
    async with SessionLocal() as db:
        stored = await db.get(Exercise, uuid.UUID(ex["id"]))
    assert stored.expected["target"] not in r.text
    assert "concepts" not in r.text and "accepted_answers" not in r.text


# ---------- full flows ----------


async def test_description_and_sentence_are_scored_end_to_end(care):  # noqa: F811
    patient, clinician, pid = care
    set_ai_provider(FakeAIProvider(fault_rate=0))
    try:
        await set_plan(
            clinician, pid, allowed_exercise_types=PHOTO_TYPES[1:], max_exercises_per_session=2
        )
        state = (await patient.post(START)).json()
        results = []
        while state["exercise"]:
            ex = state["exercise"]
            async with SessionLocal() as db:
                stored = await db.get(Exercise, uuid.UUID(ex["id"]))
            answer = stored.expected["target"]  # the model sentence covers every concept
            r = (
                await patient.post(
                    f"/api/v1/practice/exercises/{ex['id']}/responses", json={"text": answer}
                )
            ).json()
            results.append((ex["type"], r["outcome"], r["concepts_missing"]))
            state = r["state"]
    finally:
        set_ai_provider(None)
    assert results == [
        ("sentence_construction", "correct", None),
        ("picture_description", "correct", []),
    ]
    assert state["status"] == "completed"


async def test_spoken_picture_description_is_scored(care):  # noqa: F811
    patient, clinician, pid = care
    provider = FakeProvider()
    app.dependency_overrides[get_job_queue] = lambda: InlineQueue(provider)
    try:
        await set_plan(
            clinician,
            pid,
            allowed_exercise_types=["picture_description"],
            allowed_response_modes=["speech"],
        )
        ex = (await patient.post(START)).json()["exercise"]
        async with SessionLocal() as db:
            stored = await db.get(Exercise, uuid.UUID(ex["id"]))
        provider.text = stored.expected["target"]
        rec = (await upload(patient, ex["id"])).json()["recording_id"]
    finally:
        app.dependency_overrides.pop(get_job_queue, None)
    status = (await patient.get(f"/api/v1/practice/speech/{rec}")).json()
    assert status["status"] == "done" and status["result"]["outcome"] == "correct"
    assert status["result"]["concepts_missing"] == []


# ---------- AI can only choose approved catalogue images ----------


@pytest.mark.parametrize(
    ("fault", "stage"),
    [("invented_image", "schema"), ("unknown_stimulus", "clinical"), ("answer_leak", "safety")],
)
async def test_ai_cannot_select_unapproved_images(care, ai, fault, stage):  # noqa: F811
    patient, clinician, pid = care
    ai([fault, fault])
    await set_plan(clinician, pid, allowed_exercise_types=["picture_description"])
    ex = (await patient.post(START)).json()["exercise"]
    gens = await generations(pid)
    assert [g.status for g in gens] == ["rejected", "rejected"]
    assert {g.failed_stage for g in gens} == {stage}
    async with SessionLocal() as db:
        stored = await db.get(Exercise, uuid.UUID(ex["id"]))
        stim = await db.get(Stimulus, stored.stimulus_id)
    assert stored.source in {"rule", "fallback"}
    assert ex["image_url"] == stim.image_path and ex["image_url"].startswith("/stimuli/")


class WrongTypeAI(FakeAIProvider):
    """Picks a naming-only photo for a description exercise."""

    async def generate(self, request):
        result = await super().generate(request)
        data = json.loads(result.raw_output)
        data.update(stimulus_slug="photo_apple_01", difficulty=1)
        return result.__class__(json.dumps(data), result.provider, result.model)


async def test_ai_cannot_use_a_photo_without_content_for_the_type(care):  # noqa: F811
    patient, clinician, pid = care
    set_ai_provider(WrongTypeAI())
    try:
        await set_plan(clinician, pid, allowed_exercise_types=["picture_description"])
        await patient.post(START)
    finally:
        set_ai_provider(None)
    gens = await generations(pid)
    assert gens and all(g.failed_stage == "clinical" for g in gens)
    assert all(e.exercise_type == "picture_description" for e in await issued(pid))
