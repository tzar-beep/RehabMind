import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PracticeSession(Base):
    __tablename__ = "practice_sessions"
    __table_args__ = (
        # At most one active session per patient.
        Index(
            "uq_practice_sessions_one_active",
            "patient_id",
            unique=True,
            postgresql_where=text("status = 'active'"),
        ),
        # Clinician history/trends: a patient's sessions by time.
        Index("ix_practice_sessions_patient_started", "patient_id", "started_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    status: Mapped[str] = mapped_column(String(16), default="active")  # active|completed|ended
    planned_exercises: Mapped[int]
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ExerciseResponse(Base):
    """A patient's answer and its deterministic score. Doubles as the performance event log."""

    __tablename__ = "exercise_responses"
    # Clinician summaries: a patient's most recent responses.
    __table_args__ = (Index("ix_exercise_responses_patient_created", "patient_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), unique=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    mode: Mapped[str] = mapped_column(String(20))
    text: Mapped[str | None] = mapped_column(Text)
    outcome: Mapped[str] = mapped_column(String(16))  # correct|near_miss|incorrect|skipped
    score: Mapped[float] = mapped_column(Float)
    analysis: Mapped[dict[str, Any]] = mapped_column(JSONB)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
