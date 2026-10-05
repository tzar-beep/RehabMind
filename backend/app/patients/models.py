import uuid

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base, TimestampMixin
from app.users.models import User


class Patient(TimestampMixin, Base):
    __tablename__ = "patients"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), unique=True
    )
    # Pseudonymous identifier: the only patient identifier ever sent to external AI providers.
    pseudonym: Mapped[uuid.UUID] = mapped_column(unique=True, default=uuid.uuid4)

    user: Mapped[User] = relationship(lazy="joined")
