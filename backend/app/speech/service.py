"""Speech responses: upload → encrypt → queue → transcribe → delete audio → score.

Raw audio never touches the database or logs, and is deleted whether processing
succeeds or fails.
"""

import asyncio
import logging
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.scoring import normalize
from app.exercises.models import Exercise
from app.exercises.types import ResponseMode
from app.sessions import service as practice
from app.sessions.models import ExerciseResponse
from app.speech.models import AudioAsset
from app.speech.provider import SpeechProvider, Transcript
from app.storage.audio import EphemeralAudioStore
from app.workers.queue import JobQueue

log = logging.getLogger(__name__)

ALLOWED_CONTENT_TYPES = {
    "audio/webm",
    "audio/ogg",
    "audio/mp4",
    "audio/mpeg",
    "audio/wav",
    "audio/x-wav",
}
MIN_BYTES = 1_000
# A wrong transcript is worse than asking again: be strict about uncertain recognition.
NO_SPEECH_THRESHOLD = 0.6
MIN_AVG_LOGPROB = -1.0
# Whisper is known to "hear" these in silence, noise or tones (training-data artefacts).
HALLUCINATIONS = {
    "thanks for watching",
    "thank you for watching",
    "thank you",
    "please subscribe",
    "subscribe",
    "bye",
    "you",
    "music",
    "applause",
}


def unreliable_reason(t: Transcript) -> str | None:
    """Why a transcript must not be scored, or None if it is usable."""
    if t.is_empty:
        return "empty"
    if t.no_speech_prob >= NO_SPEECH_THRESHOLD:
        return "no_speech"
    if t.avg_logprob is not None and t.avg_logprob < MIN_AVG_LOGPROB:
        return "low_confidence"
    if normalize(t.text) in HALLUCINATIONS:
        return "known_hallucination"
    return None


STALE_AFTER = timedelta(minutes=10)


def base_content_type(value: str | None) -> str:
    return (value or "").split(";")[0].strip().lower()


async def accept_upload(
    db: AsyncSession,
    patient_id: uuid.UUID,
    exercise_id: uuid.UUID,
    audio: bytes,
    content_type: str,
    latency_ms: int | None,
    store: EphemeralAudioStore,
    queue: JobQueue,
    hints_used: int = 0,
) -> AudioAsset:
    exercise = (
        await db.execute(
            select(Exercise).where(Exercise.id == exercise_id, Exercise.patient_id == patient_id)
        )
    ).scalar_one_or_none()
    if exercise is None:
        raise LookupError
    if exercise.status != "pending":
        raise practice.PracticeConflict("exercise already answered")
    if ResponseMode.SPEECH not in exercise.response_modes:
        raise practice.PracticeConflict("speech not allowed for this exercise")

    object_key = await store.put(audio)
    asset = AudioAsset(
        exercise_id=exercise.id,
        patient_id=patient_id,
        object_key=object_key,
        content_type=content_type,
        size_bytes=len(audio),
        latency_ms=latency_ms,
        hints_used=hints_used,
        status="pending",
    )
    db.add(asset)
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        await store.delete(object_key)
        raise practice.PracticeConflict("a recording is already being processed") from None
    await queue.enqueue_speech(asset.id)
    return asset


async def _discard_audio(asset: AudioAsset, store: EphemeralAudioStore) -> None:
    if asset.object_key:
        try:
            await store.delete(asset.object_key)
        except Exception:
            # Bucket expiry rule removes it within a day; never retain silently.
            log.exception("audio delete failed", extra={"data": {"asset_id": str(asset.id)}})
        asset.object_key = None
        asset.deleted_at = datetime.now(UTC)


def stt_metadata(t: Transcript) -> dict[str, object]:
    return {
        "provider": t.provider,
        "model": t.model,
        "duration_s": t.duration_s,
        "no_speech_prob": t.no_speech_prob,
        "avg_logprob": t.avg_logprob,
        "low_confidence_words": t.low_confidence_words,
    }


async def process(
    db: AsyncSession, asset_id: uuid.UUID, store: EphemeralAudioStore, provider: SpeechProvider
) -> AudioAsset | None:
    asset = (
        await db.execute(select(AudioAsset).where(AudioAsset.id == asset_id).with_for_update())
    ).scalar_one_or_none()
    if asset is None or asset.status != "pending":
        return asset
    asset.status = "processing"
    await db.commit()

    transcript: Transcript | None = None
    try:
        audio = await store.get(asset.object_key or "")
        transcript = await asyncio.to_thread(provider.transcribe, audio, "en")
        del audio
    except Exception:
        log.exception("transcription failed", extra={"data": {"asset_id": str(asset.id)}})
        asset.failure_reason = "transcription_error"
    finally:
        await _discard_audio(asset, store)

    asset.processed_at = datetime.now(UTC)
    if transcript is None:
        asset.status = "failed"
    elif reason := unreliable_reason(transcript):
        # Not scored; the exercise stays open so the patient can try again or type.
        asset.status, asset.failure_reason = "no_speech", reason
    else:
        await db.commit()
        try:
            await practice.submit_response(
                db,
                asset.patient_id,
                asset.exercise_id,
                transcript.text,
                asset.latency_ms,
                hints_used=asset.hints_used,
                mode=ResponseMode.SPEECH,
                extra_analysis={"stt": stt_metadata(transcript)},
            )
            asset.response_id = await db.scalar(
                select(ExerciseResponse.id).where(ExerciseResponse.exercise_id == asset.exercise_id)
            )
            asset.status = "done"
        except (practice.PracticeConflict, LookupError):
            await db.rollback()
            asset = await db.get(AudioAsset, asset_id)
            asset.status, asset.failure_reason = "failed", "exercise_closed"
    await db.commit()
    return asset


async def sweep_stale(db: AsyncSession, store: EphemeralAudioStore) -> int:
    """Fail and delete recordings stuck in the pipeline (e.g. worker crash)."""
    cutoff = datetime.now(UTC) - STALE_AFTER
    rows = await db.execute(
        select(AudioAsset).where(
            AudioAsset.status.in_(("pending", "processing")), AudioAsset.created_at < cutoff
        )
    )
    stale = list(rows.scalars())
    for asset in stale:
        await _discard_audio(asset, store)
        asset.status, asset.failure_reason = "failed", "timed_out"
    await db.commit()
    return len(stale)
