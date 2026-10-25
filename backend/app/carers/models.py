import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PatientCarer(Base):
    """A family member or carer linked to a patient (set up by an admin).

    Carers support practice at home: they see activity and goals (never scores or answers),
    add the patient's own words, and send encouragement. They have no clinical access.
    """

    __tablename__ = "patient_carers"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    # How they know the patient, in the family's words: "daughter", "husband", "friend".
    relationship: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
