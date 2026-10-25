import uuid
from datetime import date, datetime

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class TherapyGoal(Base):
    """A goal the clinician sets with the patient, measured from practice data.

    name_words: name `target` words on their own (right the last three times), optionally
    in one picture category. practice_days: practise on `target` days in the current week.
    """

    __tablename__ = "therapy_goals"
    __table_args__ = (
        CheckConstraint("kind IN ('name_words', 'practice_days')", name="kind"),
        CheckConstraint("status IN ('active', 'achieved', 'ended')", name="status"),
        CheckConstraint("target BETWEEN 1 AND 200", name="target"),
        CheckConstraint("kind = 'name_words' OR target <= 7", name="days_in_week"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    kind: Mapped[str] = mapped_column(String(20))
    target: Mapped[int] = mapped_column(SmallInteger)
    category: Mapped[str | None] = mapped_column(String(40))
    due_on: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(12), default="active", server_default="active")
    created_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    achieved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
