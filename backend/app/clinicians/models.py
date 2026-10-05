import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin
from app.users.models import User


class Clinician(TimestampMixin, Base):
    __tablename__ = "clinicians"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True
    )

    user: Mapped[User] = relationship(lazy="joined")


class PatientClinician(Base):
    """Care-team assignment. A clinician may access only patients assigned here."""

    __tablename__ = "patient_clinicians"

    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), primary_key=True
    )
    clinician_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("clinicians.id", ondelete="CASCADE"), primary_key=True, index=True
    )
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
