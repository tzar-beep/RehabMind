import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class MoodCheckin(Base):
    """How the patient feels today, in one tap (good / okay / low). Mood after a stroke
    matters for therapy: low mood is common and affects practice. One per day."""

    __tablename__ = "mood_checkins"
    __table_args__ = (
        UniqueConstraint("patient_id", "day"),
        CheckConstraint("mood IN ('good', 'okay', 'low')", name="mood"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    day: Mapped[date] = mapped_column(Date)
    mood: Mapped[str] = mapped_column(String(8))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
