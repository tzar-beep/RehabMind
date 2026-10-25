import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, SmallInteger, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class ScriptPractice(Base):
    """One run through an everyday script ("At the café"), with how many lines the patient
    said they managed (self-report: script practice at home is not scored)."""

    __tablename__ = "script_practice"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    script_id: Mapped[str] = mapped_column(String(40))
    lines_said: Mapped[int] = mapped_column(SmallInteger)
    lines_total: Mapped[int] = mapped_column(SmallInteger)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
