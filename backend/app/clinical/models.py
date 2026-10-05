import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    SmallInteger,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ConstraintSet(Base):
    """Clinician-defined boundaries for a patient's practice.

    Immutable and versioned: a change creates a new row with version + 1. Only the latest
    version is valid for issuing exercises (enforced by a DB trigger on `exercises`).
    """

    __tablename__ = "clinical_constraint_sets"
    __table_args__ = (
        UniqueConstraint("patient_id", "version"),
        CheckConstraint(
            "min_difficulty >= 1 AND max_difficulty <= 5 AND min_difficulty <= max_difficulty",
            name="difficulty_range",
        ),
        CheckConstraint("max_exercises_per_session BETWEEN 1 AND 50", name="session_limit"),
        CheckConstraint("advance_after_correct BETWEEN 1 AND 10", name="advance_rule"),
        CheckConstraint("step_back_after_incorrect BETWEEN 1 AND 10", name="step_back_rule"),
        CheckConstraint("cardinality(allowed_exercise_types) > 0", name="has_types"),
        CheckConstraint("cardinality(allowed_response_modes) > 0", name="has_modes"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    version: Mapped[int]
    allowed_exercise_types: Mapped[list[str]] = mapped_column(ARRAY(String(40)))
    allowed_response_modes: Mapped[list[str]] = mapped_column(ARRAY(String(20)))
    # NULL = all categories in the curated library.
    allowed_categories: Mapped[list[str] | None] = mapped_column(ARRAY(String(40)))
    min_difficulty: Mapped[int] = mapped_column(SmallInteger)
    max_difficulty: Mapped[int] = mapped_column(SmallInteger)
    max_exercises_per_session: Mapped[int] = mapped_column(SmallInteger)
    advance_after_correct: Mapped[int] = mapped_column(SmallInteger, default=3)
    step_back_after_incorrect: Mapped[int] = mapped_column(SmallInteger, default=2)
    note: Mapped[str | None] = mapped_column(String(500))
    created_by_user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
