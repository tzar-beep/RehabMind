import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base, TimestampMixin


class Stimulus(TimestampMixin, Base):
    """Curated, licensed picture library. Synced from stimuli_catalog.json; never AI-generated."""

    __tablename__ = "stimuli"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    slug: Mapped[str] = mapped_column(String(64), unique=True)
    target: Mapped[str] = mapped_column(String(64))
    accepted_answers: Mapped[list[str]] = mapped_column(ARRAY(String(64)))
    category: Mapped[str] = mapped_column(String(40), index=True)
    difficulty: Mapped[int] = mapped_column(SmallInteger, index=True)
    image_path: Mapped[str] = mapped_column(String(200))
    license: Mapped[str] = mapped_column(String(40))
    catalog_version: Mapped[int]
    is_active: Mapped[bool] = mapped_column(default=True)


class Exercise(Base):
    """An exercise issued to a patient.

    Rows are created only by `app.exercises.issuer.issue`. A DB trigger independently
    rejects any row that violates the patient's latest clinical constraint set.
    """

    __tablename__ = "exercises"
    __table_args__ = (UniqueConstraint("session_id", "position"),)

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"), index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    constraint_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clinical_constraint_sets.id"))
    position: Mapped[int] = mapped_column(SmallInteger)
    exercise_type: Mapped[str] = mapped_column(String(40))
    difficulty: Mapped[int] = mapped_column(SmallInteger)
    response_modes: Mapped[list[str]] = mapped_column(ARRAY(String(20)))
    stimulus_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("stimuli.id"))
    # Safe to show the patient.
    content: Mapped[dict[str, Any]] = mapped_column(JSONB)
    # Server-only scoring key (never serialized to the patient).
    expected: Mapped[dict[str, Any]] = mapped_column(JSONB)
    source: Mapped[str] = mapped_column(String(20))  # rule | fallback | ai
    generator_version: Mapped[str] = mapped_column(String(40))
    status: Mapped[str] = mapped_column(String(16), default="pending")
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
