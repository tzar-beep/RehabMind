import uuid
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.ai import feedback as ai_feedback
from app.ai.provider import get_ai_provider
from app.auth.deps import DbDep, PatientUser
from app.clinical.service import latest_constraints
from app.exercises.generator import NoSafeExercise
from app.exercises.models import Exercise
from app.exercises.types import CHOICE_TYPES, NAMING_FAMILY
from app.patients.access import accessible_patients
from app.patients.models import Patient
from app.sessions import resets, service
from app.sessions.models import ExerciseResponse, PracticeSession

router = APIRouter(prefix="/practice", tags=["practice"])


class ExerciseOut(BaseModel):
    """Patient-facing view. Never includes the scoring key."""

    id: str
    position: int
    type: str
    prompt: str
    instructions: str
    image_url: str | None
    response_modes: list[str]
    # Progressive hints, revealed one at a time on request (meaning, then first sound).
    cues: list[str]
    # Sentence construction: the word bank (already scrambled; never in answer order).
    words: list[str] | None = None
    # "photo" (real-world photograph) or "icon" (line drawing).
    image_kind: str = "icon"
    # Word repetition and word recognition: the word to say or to find.
    word: str | None = None
    # Picture-choice types: the pictures to choose from (word = what a tap answers).
    options: list[dict[str, str]] | None = None


class Summary(BaseModel):
    practiced: int
    correct: int
    near_miss: int


class SessionState(BaseModel):
    session_id: str
    status: str
    total: int
    exercise: ExerciseOut | None
    summary: Summary | None


class ResponseIn(BaseModel):
    text: str | None = Field(default=None, max_length=200)
    skipped: bool = False
    hints_used: int = Field(default=0, ge=0, le=2)
    latency_ms: int | None = Field(default=None, ge=0, le=3_600_000)
    # Return the score without preparing the next exercise (the client fetches it next).
    defer_next: bool = False


class ResponseResult(BaseModel):
    outcome: Literal["correct", "near_miss", "incorrect", "skipped"]
    target: str
    heard: str | None = None  # transcript, for speech responses
    # Picture description: which key ideas the answer mentioned / missed.
    concepts_matched: list[str] | None = None
    concepts_missing: list[str] | None = None
    state: SessionState


class Resumable(BaseModel):
    session_id: str
    answered: int


class PracticeStatus(BaseModel):
    has_plan: bool
    has_active_session: bool
    # A session stopped early in the last 30 minutes that can be reopened ("Keep going").
    resumable: Resumable | None = None


class RecentSession(BaseModel):
    started_at: datetime
    answered: int


class PracticeActivity(BaseModel):
    """The patient's own practice activity. Counts only: no scores or accuracy."""

    sessions_completed: int
    pictures_practised: int
    recent: list[RecentSession]


ACTIVITY_DAYS = 8  # a week plus a day, so the caller can group by its local date


_NO_PLAN = HTTPException(status.HTTP_409_CONFLICT, "Your practice plan is not ready yet.")
_NO_EXERCISE = HTTPException(
    status.HTTP_409_CONFLICT, "No practice is available right now. Please contact your care team."
)


async def _me(user: PatientUser, db: DbDep) -> Patient:
    patient = (await db.execute(accessible_patients(user))).scalar_one_or_none()
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient profile not found.")
    return patient


async def _state(db: DbDep, session: PracticeSession) -> SessionState:
    exercise: Exercise | None = await service.pending_exercise(db, session.id)
    summary = None
    if session.status != "active":
        counts = await service.outcome_counts(db, session.id)
        summary = Summary(
            practiced=sum(counts.values()),
            correct=counts.get("correct", 0),
            near_miss=counts.get("near_miss", 0),
        )
    return SessionState(
        session_id=str(session.id),
        status=session.status,
        total=session.planned_exercises,
        exercise=ExerciseOut(
            id=str(exercise.id),
            position=exercise.position,
            type=exercise.exercise_type,
            prompt=exercise.content["prompt"],
            instructions=exercise.content["instructions"],
            image_url=exercise.content.get("image_url"),
            response_modes=exercise.response_modes,
            cues=exercise.content.get("cues", []),
            words=exercise.content.get("words"),
            image_kind=exercise.content.get("image_kind", "icon"),
            word=exercise.content.get("word"),
            options=exercise.content.get("options"),
        )
        if exercise
        else None,
        summary=summary,
    )


@router.get("/status", response_model=PracticeStatus)
async def practice_status(user: PatientUser, db: DbDep) -> PracticeStatus:
    patient = await _me(user, db)
    stopped = await service.resumable_session(db, patient.id)
    return PracticeStatus(
        has_plan=await latest_constraints(db, patient.id) is not None,
        has_active_session=await service.active_session(db, patient.id) is not None,
        resumable=Resumable(
            session_id=str(stopped.id),
            answered=sum((await service.outcome_counts(db, stopped.id)).values()),
        )
        if stopped
        else None,
    )


class RecapWord(BaseModel):
    word: str
    image_url: str | None
    outcome: Literal["correct", "near_miss", "incorrect", "skipped"]


@router.get("/sessions/{session_id}/recap", response_model=list[RecapWord])
async def session_recap(session_id: uuid.UUID, user: PatientUser, db: DbDep) -> list[RecapWord]:
    """The one-word exercises answered in a session, in order: for the end-of-session
    recap ("Words you named today"), including answers given before a "Keep going"."""
    session = await db.get(PracticeSession, session_id)
    if session is None or session.patient_id != (await _me(user, db)).id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found.")
    rows = await db.execute(
        select(Exercise, ExerciseResponse.outcome)
        .join(ExerciseResponse, ExerciseResponse.exercise_id == Exercise.id)
        .where(
            Exercise.session_id == session_id,
            Exercise.exercise_type.in_(sorted(NAMING_FAMILY | CHOICE_TYPES)),
        )
        .order_by(Exercise.position)
    )
    return [
        RecapWord(
            word=ex.expected["target"],
            image_url=ex.content.get("image_url")
            or next(
                (
                    o["image_url"]
                    for o in ex.content.get("options") or []
                    if o["word"] == ex.expected["target"]
                ),
                None,
            ),
            outcome=outcome,
        )
        for ex, outcome in rows.all()
    ]


@router.post("/sessions/{session_id}/resume", response_model=SessionState)
async def resume_session(session_id: uuid.UUID, user: PatientUser, db: DbDep) -> SessionState:
    """Undo "Stop for today" within 30 minutes: carry on where the patient left off."""
    patient = await _me(user, db)
    try:
        session = await service.resume(db, patient.id, session_id, user.id)
    except service.NotResumable:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "That practice can't be continued. Start a new one."
        ) from None
    except service.NoPlan:
        raise _NO_PLAN from None
    except NoSafeExercise:
        raise _NO_EXERCISE from None
    return await _state(db, session)


@router.get("/activity", response_model=PracticeActivity)
async def practice_activity(user: PatientUser, db: DbDep) -> PracticeActivity:
    patient = await _me(user, db)
    reset_at = await resets.cutoff(db, patient.id)
    completed = await db.scalar(
        select(func.count())
        .select_from(PracticeSession)
        .where(
            PracticeSession.patient_id == patient.id,
            PracticeSession.status == "completed",
            resets.after(PracticeSession.started_at, reset_at),
        )
    )
    practised = await db.scalar(
        select(func.count())
        .select_from(ExerciseResponse)
        .where(
            ExerciseResponse.patient_id == patient.id,
            resets.after(ExerciseResponse.created_at, reset_at),
        )
    )
    since = max(
        datetime.now(UTC) - timedelta(days=ACTIVITY_DAYS),
        reset_at or datetime.min.replace(tzinfo=UTC),
    )
    answered = (
        select(func.count())
        .select_from(ExerciseResponse)
        .join(Exercise, Exercise.id == ExerciseResponse.exercise_id)
        .where(Exercise.session_id == PracticeSession.id)
        .scalar_subquery()
    )
    rows = await db.execute(
        select(PracticeSession.started_at, answered)
        .where(PracticeSession.patient_id == patient.id, PracticeSession.started_at >= since)
        .order_by(PracticeSession.started_at)
    )
    return PracticeActivity(
        sessions_completed=completed or 0,
        pictures_practised=practised or 0,
        recent=[RecentSession(started_at=t, answered=n) for t, n in rows],
    )


@router.post("/sessions", response_model=SessionState)
async def start_session(user: PatientUser, db: DbDep) -> SessionState:
    """Start a session, or resume the active one."""
    patient = await _me(user, db)
    try:
        session = await service.start_or_resume(db, patient.id, user.id)
    except service.NoPlan:
        raise _NO_PLAN from None
    except NoSafeExercise:
        raise _NO_EXERCISE from None
    return await _state(db, session)


@router.get("/sessions/current", response_model=SessionState)
async def current_session(user: PatientUser, db: DbDep) -> SessionState:
    patient = await _me(user, db)
    session = await service.active_session(db, patient.id)
    if session is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No active practice session.")
    return await _state(db, session)


@router.post("/sessions/current/end", status_code=status.HTTP_204_NO_CONTENT)
async def end_current_session(user: PatientUser, db: DbDep) -> None:
    await service.end_session(db, (await _me(user, db)).id)


class RatingIn(BaseModel):
    rating: Literal["too_easy", "just_right", "too_hard"]


@router.put("/sessions/{session_id}/rating", status_code=status.HTTP_204_NO_CONTENT)
async def rate_session(session_id: uuid.UUID, body: RatingIn, user: PatientUser, db: DbDep) -> None:
    """How hard the finished session felt. Optional; can be changed until the next one."""
    session = await db.get(PracticeSession, session_id)
    if session is None or session.patient_id != (await _me(user, db)).id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found.")
    if session.status == "active":
        raise HTTPException(status.HTTP_409_CONFLICT, "Finish the session first.")
    session.difficulty_rating = body.rating
    await db.commit()


@router.post("/exercises/{exercise_id}/responses", response_model=ResponseResult)
async def respond(
    exercise_id: uuid.UUID, body: ResponseIn, user: PatientUser, db: DbDep
) -> ResponseResult:
    patient = await _me(user, db)
    try:
        exercise, result, session = await service.submit_response(
            db,
            patient.id,
            exercise_id,
            None if body.skipped else body.text,
            body.latency_ms,
            hints_used=body.hints_used,
            issue_next_exercise=not body.defer_next,
        )
    except LookupError:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exercise not found.") from None
    except service.PracticeConflict:
        raise HTTPException(status.HTTP_409_CONFLICT, "This exercise is already done.") from None
    except service.NoPlan:
        raise _NO_PLAN from None
    except NoSafeExercise:
        raise _NO_EXERCISE from None
    return ResponseResult(
        outcome=result.outcome,
        target=exercise.expected["target"],
        concepts_matched=result.details.get("concepts_matched"),
        concepts_missing=result.details.get("concepts_missing"),
        state=await _state(db, session),
    )


class AIFeedbackOut(BaseModel):
    """A short supportive tip about an answer that is already scored, or nothing."""

    feedback: str | None
    hint: str | None


@router.post("/exercises/{exercise_id}/feedback", response_model=AIFeedbackOut)
async def ai_feedback_for(exercise_id: uuid.UUID, user: PatientUser, db: DbDep) -> AIFeedbackOut:
    """GenAI use case 2. Called after the standard feedback is on screen, so a slow or failed
    model never delays the patient. The deterministic score is never changed."""
    patient = await _me(user, db)
    # Row lock: simultaneous requests for the same answer (e.g. a double render) wait for
    # the first one, then reuse its result instead of calling the model again.
    exercise = await db.scalar(
        select(Exercise)
        .where(Exercise.id == exercise_id, Exercise.patient_id == patient.id)
        .with_for_update()
    )
    if exercise is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Exercise not found.")
    response = await db.scalar(
        select(ExerciseResponse).where(ExerciseResponse.exercise_id == exercise.id)
    )
    if response is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "This exercise has no answer yet.")
    provider = get_ai_provider()
    out = None
    if provider is not None:
        out = await ai_feedback.feedback_for(db, provider, exercise, response)
    return AIFeedbackOut(
        feedback=out.feedback if out else None, hint=out.optional_hint if out else None
    )
