"""Practice loop: start/resume → exercise → response → score → profile → next exercise."""

import uuid
from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.analysis.scoring import ScoreResult, score_naming
from app.audit import service as audit
from app.clinical.service import latest_constraints
from app.exercises import generator
from app.exercises.generator import NoSafeExercise
from app.exercises.issuer import ConstraintViolation, issue
from app.exercises.models import Exercise
from app.exercises.types import ExerciseType, ResponseMode
from app.performance.progression import apply_outcome, get_profile
from app.sessions.models import ExerciseResponse, PracticeSession


class NoPlan(Exception):
    pass


class PracticeConflict(Exception):
    pass


async def active_session(db: AsyncSession, patient_id: uuid.UUID) -> PracticeSession | None:
    stmt = select(PracticeSession).where(
        PracticeSession.patient_id == patient_id, PracticeSession.status == "active"
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def pending_exercise(db: AsyncSession, session_id: uuid.UUID) -> Exercise | None:
    stmt = select(Exercise).where(Exercise.session_id == session_id, Exercise.status == "pending")
    return (await db.execute(stmt)).scalar_one_or_none()


async def count_exercises(db: AsyncSession, session_id: uuid.UUID) -> int:
    return (
        await db.scalar(
            select(func.count()).select_from(Exercise).where(Exercise.session_id == session_id)
        )
        or 0
    )


async def issue_next(db: AsyncSession, session: PracticeSession) -> Exercise | None:
    """Issue the next exercise, or complete the session when its limit is reached."""
    cs = await latest_constraints(db, session.patient_id)
    if cs is None:
        raise NoPlan
    position = await count_exercises(db, session.id) + 1
    if position > min(session.planned_exercises, cs.max_exercises_per_session):
        session.status = "completed"
        session.completed_at = datetime.now(UTC)
        return None

    profile = await get_profile(db, session.patient_id, ExerciseType.PICTURE_NAMING, cs)
    try:
        proposal = await generator.propose_next(
            db, session.patient_id, session.id, cs, profile.target_difficulty
        )
        return await issue(db, session, cs, proposal, position)
    except (ConstraintViolation, NoSafeExercise) as e:
        reasons = e.reasons if isinstance(e, ConstraintViolation) else [str(e)]
        await audit.record(
            db,
            "exercise.rejected",
            "failure",
            target_type="session",
            target_id=session.id,
            details={"reasons": reasons, "constraint_version": cs.version},
            commit=False,
        )
    try:
        return await issue(db, session, cs, await generator.fallback(db, session.id, cs), position)
    except ConstraintViolation as e:
        raise NoSafeExercise(str(e)) from e


async def start_or_resume(
    db: AsyncSession, patient_id: uuid.UUID, actor_user_id: uuid.UUID
) -> PracticeSession:
    session = await active_session(db, patient_id)
    if session is None:
        cs = await latest_constraints(db, patient_id)
        if cs is None:
            raise NoPlan
        session = PracticeSession(
            patient_id=patient_id, planned_exercises=cs.max_exercises_per_session
        )
        db.add(session)
        try:
            await db.flush()
        except IntegrityError:  # concurrent start: reuse the session that won
            await db.rollback()
            return await start_or_resume(db, patient_id, actor_user_id)
        await audit.record(
            db,
            "practice.session_started",
            "success",
            actor_user_id=actor_user_id,
            target_type="session",
            target_id=session.id,
            details={"constraint_version": cs.version},
            commit=False,
        )
    if await pending_exercise(db, session.id) is None:
        await issue_next(db, session)
    await db.commit()
    return session


async def submit_response(
    db: AsyncSession,
    patient_id: uuid.UUID,
    exercise_id: uuid.UUID,
    text: str | None,
    latency_ms: int | None,
    *,
    mode: ResponseMode = ResponseMode.TEXT,
    extra_analysis: dict[str, object] | None = None,
) -> tuple[Exercise, ScoreResult, PracticeSession]:
    stmt = (
        select(Exercise)
        .where(Exercise.id == exercise_id, Exercise.patient_id == patient_id)
        .with_for_update()
    )
    exercise = (await db.execute(stmt)).scalar_one_or_none()
    if exercise is None:
        raise LookupError
    session = await db.get(PracticeSession, exercise.session_id)
    if exercise.status != "pending" or session is None or session.status != "active":
        raise PracticeConflict("exercise already answered or session not active")
    if mode not in exercise.response_modes:
        raise PracticeConflict(f"{mode} responses not allowed for this exercise")

    result = score_naming(text, exercise.expected["target"], exercise.expected["accepted_answers"])
    exercise.status = "skipped" if result.outcome == "skipped" else "answered"
    db.add(
        ExerciseResponse(
            exercise_id=exercise.id,
            patient_id=patient_id,
            mode=mode,
            text=(text or "").strip()[:200] or None,
            outcome=result.outcome,
            score=result.score,
            analysis={
                "method": "rules-v1",
                "match_type": result.match_type,
                "matched": result.matched,
                "similarity": result.similarity,
                **(extra_analysis or {}),
            },
            latency_ms=latency_ms,
        )
    )

    cs = await latest_constraints(db, patient_id)
    if cs is None:
        raise NoPlan
    profile = await get_profile(db, patient_id, exercise.exercise_type, cs)
    apply_outcome(profile, result.outcome, cs)
    await issue_next(db, session)
    await db.commit()
    return exercise, result, session


async def end_session(db: AsyncSession, patient_id: uuid.UUID) -> None:
    session = await active_session(db, patient_id)
    if session is None:
        return
    session.status = "ended"
    session.completed_at = datetime.now(UTC)
    if (ex := await pending_exercise(db, session.id)) is not None:
        ex.status = "cancelled"
    await db.commit()


async def outcome_counts(db: AsyncSession, session_id: uuid.UUID) -> dict[str, int]:
    rows = await db.execute(
        select(ExerciseResponse.outcome, func.count())
        .join(Exercise, Exercise.id == ExerciseResponse.exercise_id)
        .where(Exercise.session_id == session_id)
        .group_by(ExerciseResponse.outcome)
    )
    return {outcome: n for outcome, n in rows.all()}
