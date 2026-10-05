import uuid
from datetime import UTC, datetime, timedelta

import pytest
from cryptography.exceptions import InvalidTag
from sqlalchemy import select, update

from app.core.db import SessionLocal
from app.exercises.models import Exercise
from app.main import app
from app.sessions.models import ExerciseResponse
from app.speech import service as speech
from app.speech.models import AudioAsset
from app.speech.provider import Transcript
from app.storage.audio import get_audio_store
from app.workers.queue import get_job_queue
from tests.test_practice import START, as_user, care, set_plan, target_of  # noqa: F401

AUDIO = b"RIFF" + b"\x01" * 4000  # opaque bytes; the fake provider never decodes them


class FakeProvider:
    def __init__(self) -> None:
        self.text: str | None = ""
        self.no_speech_prob = 0.01
        self.fail = False

    def transcribe(self, audio: bytes, language: str) -> Transcript:
        assert audio == AUDIO and language == "en"  # decrypted correctly
        if self.fail:
            raise RuntimeError("decoder error")
        return Transcript(self.text or "", "fake", "fake-1", 1.2, self.no_speech_prob, -0.2, [])


class InlineQueue:
    """Runs the worker job immediately, against real storage."""

    def __init__(self, provider: FakeProvider, run: bool = True) -> None:
        self.provider, self.run = provider, run

    async def enqueue_speech(self, asset_id: uuid.UUID) -> None:
        if self.run:
            async with SessionLocal() as db:
                await speech.process(db, asset_id, get_audio_store(), self.provider)


@pytest.fixture
def stt():
    provider = FakeProvider()
    app.dependency_overrides[get_job_queue] = lambda: InlineQueue(provider)
    yield provider
    app.dependency_overrides.pop(get_job_queue, None)


async def speech_plan(care):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(clinician, pid, allowed_response_modes=["text", "speech"])
    state = (await patient.post(START)).json()
    return patient, state["exercise"]


async def upload(client, exercise_id, data=AUDIO, ctype="audio/webm;codecs=opus"):
    return await client.post(
        f"/api/v1/practice/exercises/{exercise_id}/speech",
        files={"audio": ("rec.webm", data, ctype)},
        data={"latency_ms": "2500"},
    )


async def asset_row(recording_id: str) -> AudioAsset:
    async with SessionLocal() as db:
        return await db.get(AudioAsset, uuid.UUID(recording_id))


# ---------- encryption ----------


async def test_audio_is_encrypted_at_rest_and_bound_to_its_key():
    store = get_audio_store()
    key = await store.put(AUDIO)
    raw = store.store.get(key)
    assert AUDIO not in raw and raw[:2] == b"v1"
    assert await store.get(key) == AUDIO
    other = await store.put(b"x" * 2000)
    store.store.put(other, raw)  # swap ciphertexts between objects
    with pytest.raises(InvalidTag):
        await store.get(other)
    await store.delete(key)
    await store.delete(other)
    assert not await store.exists(key)


# ---------- pipeline ----------


async def test_speech_answer_is_transcribed_scored_and_audio_deleted(care, stt):  # noqa: F811
    patient, ex = await speech_plan(care)
    stt.text = f" A {await target_of(ex['id'])}. "
    r = await upload(patient, ex["id"])
    assert r.status_code == 202
    rec = r.json()["recording_id"]

    asset = await asset_row(rec)
    assert asset.status == "done"
    assert asset.object_key is None and asset.deleted_at is not None
    assert asset.content_type == "audio/webm"

    status = (await patient.get(f"/api/v1/practice/speech/{rec}")).json()
    assert status["status"] == "done"
    assert status["result"]["outcome"] == "correct"
    assert status["result"]["heard"] == stt.text.strip()
    assert status["result"]["state"]["exercise"]["position"] == 2

    async with SessionLocal() as db:
        resp = (await db.execute(select(ExerciseResponse))).scalar_one()
    assert resp.mode == "speech" and resp.latency_ms == 2500
    assert resp.analysis["stt"]["provider"] == "fake"


async def test_no_speech_keeps_exercise_open_for_retry(care, stt):  # noqa: F811
    patient, ex = await speech_plan(care)
    stt.text, stt.no_speech_prob = "", 0.95
    rec = (await upload(patient, ex["id"])).json()["recording_id"]
    assert (await patient.get(f"/api/v1/practice/speech/{rec}")).json() == {
        "status": "no_speech",
        "result": None,
    }
    assert (await asset_row(rec)).object_key is None
    stt.text, stt.no_speech_prob = "zzzz", 0.01
    rec2 = (await upload(patient, ex["id"])).json()["recording_id"]
    assert (await asset_row(rec2)).status == "done"


async def test_failed_transcription_still_deletes_audio(care, stt):  # noqa: F811
    patient, ex = await speech_plan(care)
    stt.fail = True
    rec = (await upload(patient, ex["id"])).json()["recording_id"]
    asset = await asset_row(rec)
    assert (asset.status, asset.failure_reason) == ("failed", "transcription_error")
    assert asset.object_key is None
    async with SessionLocal() as db:
        assert (await db.get(Exercise, uuid.UUID(ex["id"]))).status == "pending"


async def test_one_recording_in_flight_per_exercise(care):  # noqa: F811
    app.dependency_overrides[get_job_queue] = lambda: InlineQueue(FakeProvider(), run=False)
    try:
        patient, ex = await speech_plan(care)
        assert (await upload(patient, ex["id"])).status_code == 202
        assert (await upload(patient, ex["id"])).status_code == 409
    finally:
        app.dependency_overrides.pop(get_job_queue, None)


async def test_stale_recordings_are_failed_and_deleted(care):  # noqa: F811
    app.dependency_overrides[get_job_queue] = lambda: InlineQueue(FakeProvider(), run=False)
    try:
        patient, ex = await speech_plan(care)
        rec = (await upload(patient, ex["id"])).json()["recording_id"]
    finally:
        app.dependency_overrides.pop(get_job_queue, None)
    key = (await asset_row(rec)).object_key
    async with SessionLocal() as db:
        await db.execute(
            update(AudioAsset).values(created_at=datetime.now(UTC) - timedelta(hours=1))
        )
        await db.commit()
        assert await speech.sweep_stale(db, get_audio_store()) == 1
    assert not await get_audio_store().exists(key)
    assert (await asset_row(rec)).failure_reason == "timed_out"


# ---------- validation and isolation ----------


async def test_speech_rejected_when_clinician_allows_text_only(care, stt):  # noqa: F811
    patient, clinician, pid = care
    await set_plan(clinician, pid, allowed_response_modes=["text"])
    ex = (await patient.post(START)).json()["exercise"]
    assert ex["response_modes"] == ["text"]
    assert (await upload(patient, ex["id"])).status_code == 409


@pytest.mark.parametrize(
    ("size", "ctype", "code"),
    [
        (4000, "text/plain", 415),
        (4000, "application/octet-stream", 415),
        (500, "audio/webm", 422),
        (2_000_001, "audio/webm", 413),
    ],
)
async def test_upload_validation(care, stt, size, ctype, code):  # noqa: F811
    patient, ex = await speech_plan(care)
    assert (await upload(patient, ex["id"], b"x" * size, ctype)).status_code == code


async def test_recordings_are_patient_isolated(care, stt):  # noqa: F811
    from app.users.models import Role
    from tests.conftest import create_user

    patient, ex = await speech_plan(care)
    stt.text = "zzzz"
    rec = (await upload(patient, ex["id"])).json()["recording_id"]
    await create_user("other@x.test", Role.PATIENT)
    other = await as_user("other@x.test")
    assert (await other.get(f"/api/v1/practice/speech/{rec}")).status_code == 404
    state = (await patient.get("/api/v1/practice/sessions/current")).json()
    assert (await upload(other, state["exercise"]["id"])).status_code == 404
