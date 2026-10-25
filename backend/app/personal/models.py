import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, LargeBinary, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class PersonalPhoto(Base):
    """The photo behind one of a patient's own words, encrypted (AES-256-GCM) and stored
    re-encoded, without location or camera metadata. Deleting the word deletes the photo."""

    __tablename__ = "personal_photos"

    stimulus_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("stimuli.id", ondelete="CASCADE"), primary_key=True
    )
    data: Mapped[bytes] = mapped_column(LargeBinary)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
