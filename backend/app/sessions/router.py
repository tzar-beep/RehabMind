import uuid
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.auth.deps import DbDep, PatientUser
from app.clinical.service import latest_constraints
from app.exercises.generator import NoSafeExercise
from app.exercises.models import Exercise
from app.patients.access import accessible_patients
from app.patients.models import Patient
from app.sessions import service
from app.sessions.models import PracticeSession

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


class ResponseResult(BaseModel):
    outcome: Literal["correct", "near_miss", "incorrect", "skipped"]
    target: str
    heard: str | None = None  # transcript, for speech responses
    state: SessionState


class PracticeStatus(BaseModel):
    has_plan: bool
    has_active_session: bool


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
        )
        if exercise
        else None,
        summary=summary,
    )


@router.get("/status", response_model=PracticeStatus)
async def practice_status(user: PatientUser, db: DbDep) -> PracticeStatus:
    patient = await _me(user, db)
    return PracticeStatus(
        has_plan=await latest_constraints(db, patient.id) is not None,
        has_active_session=await service.active_session(db, patient.id) is not None,
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
        state=await _state(db, session),
    )
