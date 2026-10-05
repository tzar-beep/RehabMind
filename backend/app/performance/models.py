import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PerformanceProfile(Base):
    """Rolling per-exercise-type performance used for personalization, not diagnosis."""

    __tablename__ = "performance_profiles"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True
    )
    exercise_type: Mapped[str] = mapped_column(String(40), primary_key=True)
    # Working level proposed by the progression rule; always clamped to constraints.
    target_difficulty: Mapped[int] = mapped_column(SmallInteger)
    consecutive_correct: Mapped[int] = mapped_column(SmallInteger, default=0)
    consecutive_incorrect: Mapped[int] = mapped_column(SmallInteger, default=0)
    total_attempts: Mapped[int] = mapped_column(default=0)
    total_correct: Mapped[int] = mapped_column(default=0)
    recent_outcomes: Mapped[list[str]] = mapped_column(JSONB, default=list)  # newest last, max 20
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
