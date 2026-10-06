import uuid
from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from redis.asyncio import Redis

from app.auth.deps import DbDep, PatientUser, SettingsDep
from app.auth.rate_limit import within_limit
from app.core.redis import get_redis
from app.exercises.models import Exercise
from app.sessions import service as practice
from app.sessions.models import ExerciseResponse, PracticeSession
from app.sessions.router import ResponseResult, _me, _state
from app.speech import service as speech
from app.speech.models import AudioAsset
from app.storage.audio import EphemeralAudioStore, get_audio_store
from app.workers.queue import JobQueue, get_job_queue

router = APIRouter(prefix="/practice", tags=["speech"])

# Generous for real use (≈ one attempt every 2 s), but bounds storage/STT abuse.
UPLOADS_PER_MINUTE = 30


class SpeechAccepted(BaseModel):
    recording_id: str


class SpeechStatus(BaseModel):
    status: Literal["pending", "processing", "done", "no_speech", "failed"]
    result: ResponseResult | None = None


@router.post(
    "/exercises/{exercise_id}/speech",
    response_model=SpeechAccepted,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_speech(
    exercise_id: uuid.UUID,
    audio: UploadFile,
    user: PatientUser,
    db: DbDep,
    settings: SettingsDep,
    store: Annotated[EphemeralAudioStore, Depends(get_audio_store)],
    queue: Annotated[JobQueue, Depends(get_job_queue)],
    redis: Annotated[Redis, Depends(get_redis)],
    latency_ms: Annotated[int | None, Form(ge=0, le=3_600_000)] = None,
    hints_used: Annotated[int, Form(ge=0, le=2)] = 0,
) -> SpeechAccepted:
    content_type = speech.base_content_type(audio.content_type)
    if content_type not in speech.ALLOWED_CONTENT_TYPES:
        raise HTTPException(status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, "Unsupported audio format.")
    data = await audio.read(settings.audio_max_bytes + 1)
    if len(data) > settings.audio_max_bytes:
        raise HTTPException(status.HTTP_413_CONTENT_TOO_LARGE, "Recording is too long.")
    if len(data) < speech.MIN_BYTES:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Recording is too short.")

    patient = await _me(user, db)
    if not await within_limit(redis, f"speech:{patient.id}", UPLOADS_PER_MINUTE, 60):
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many recordings. Please wait a moment."
        )
    try:
        asset = await speech.accept_upload(
            db, patient.id, exercise_id, data, content_type, latency_ms, store, queue, hints_used
        )
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exercise not found.") from None
    except practice.PracticeConflict as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e).capitalize() + ".") from None
    finally:
        del data
    return SpeechAccepted(recording_id=str(asset.id))


@router.get("/speech/{recording_id}", response_model=SpeechStatus)
async def speech_status(recording_id: uuid.UUID, user: PatientUser, db: DbDep) -> SpeechStatus:
    patient = await _me(user, db)
    asset = await db.get(AudioAsset, recording_id)
    if asset is None or asset.patient_id != patient.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Recording not found.")
    if asset.status != "done" or asset.response_id is None:
        return SpeechStatus(status=asset.status)  # type: ignore[arg-type]

    response = await db.get(ExerciseResponse, asset.response_id)
    exercise = await db.get(Exercise, asset.exercise_id)
    session = await db.get(PracticeSession, exercise.session_id)  # type: ignore[union-attr]
    return SpeechStatus(
        status="done",
        result=ResponseResult(
            outcome=response.outcome,  # type: ignore[union-attr,arg-type]
            target=exercise.expected["target"],  # type: ignore[union-attr]
            heard=response.text,  # type: ignore[union-attr]
            concepts_matched=response.analysis.get("concepts_matched"),  # type: ignore[union-attr]
            concepts_missing=response.analysis.get("concepts_missing"),  # type: ignore[union-attr]
            state=await _state(db, session),  # type: ignore[arg-type]
        ),
    )
