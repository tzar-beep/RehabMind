"""Progress resets: a clinician-initiated "fresh start" that deletes nothing.

Every summary of a patient's practice counts only activity at or after their latest reset.
Sessions, answers, audio lifecycle rows and AI logs from before stay stored for audit.
"""

import uuid
from datetime import datetime

from sqlalchemy import ColumnElement, delete, func, or_, select, true
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import service as audit
from app.performance.models import PerformanceProfile
from app.sessions import service
from app.sessions.models import ProgressReset


async def latest_reset(db: AsyncSession, patient_id: uuid.UUID) -> ProgressReset | None:
    return await db.scalar(
        select(ProgressReset)
        .where(ProgressReset.patient_id == patient_id)
        .order_by(ProgressReset.created_at.desc())
        .limit(1)
    )


async def cutoff(db: AsyncSession, patient_id: uuid.UUID) -> datetime | None:
    """Practice before this moment no longer counts (None: never reset)."""
    return await db.scalar(
        select(func.max(ProgressReset.created_at)).where(ProgressReset.patient_id == patient_id)
    )


def cutoffs_subquery():
    """Latest reset per patient, for queries over several patients at once."""
    return (
        select(
            ProgressReset.patient_id.label("patient_id"),
            func.max(ProgressReset.created_at).label("reset_at"),
        )
        .group_by(ProgressReset.patient_id)
        .subquery()
    )


def since(column, reset_at) -> ColumnElement[bool]:
    """SQL form, for a per-patient `reset_at` column from `cutoffs_subquery` (may be NULL)."""
    return or_(reset_at.is_(None), column >= reset_at)


def after(column, reset_at: datetime | None) -> ColumnElement[bool]:
    """Python form, for one patient's `cutoff` value."""
    return column >= reset_at if reset_at else true()


async def reset_progress(
    db: AsyncSession, patient_id: uuid.UUID, actor_id: uuid.UUID, reason: str
) -> ProgressReset:
    # An open session would mix old and new practice; close it first.
    await service.end_session(db, patient_id)
    profiles = (
        await db.scalars(
            select(PerformanceProfile).where(PerformanceProfile.patient_id == patient_id)
        )
    ).all()
    previous = {p.exercise_type: p.target_difficulty for p in profiles}
    # Working levels are derived state: dropping them restarts each type at the
    # clinician's minimum difficulty on the next exercise.
    await db.execute(delete(PerformanceProfile).where(PerformanceProfile.patient_id == patient_id))
    reset = ProgressReset(
        patient_id=patient_id, reset_by=actor_id, reason=reason, previous_levels=previous
    )
    db.add(reset)
    await db.flush()
    await audit.record(
        db,
        "patient.progress_reset",
        "success",
        actor_user_id=actor_id,
        target_type="patient",
        target_id=patient_id,
        details={"previous_levels": previous},
        commit=False,
    )
    await db.commit()
    await db.refresh(reset)
    return reset
