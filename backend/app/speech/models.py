import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, func, text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AudioAsset(Base):
    """Lifecycle record for one recording. Holds no audio: the encrypted object is deleted
    as soon as processing ends (`object_key` cleared, `deleted_at` set)."""

    __tablename__ = "audio_assets"
    __table_args__ = (
        # One recording in flight per exercise.
        Index(
            "uq_audio_assets_one_in_flight",
            "exercise_id",
            unique=True,
            postgresql_where=text("status IN ('pending', 'processing')"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("exercises.id", ondelete="CASCADE"), index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    # pending | processing | done | no_speech | failed
    status: Mapped[str] = mapped_column(String(16), default="pending")
    object_key: Mapped[str | None] = mapped_column(String(80))
    content_type: Mapped[str] = mapped_column(String(60))
    size_bytes: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    failure_reason: Mapped[str | None] = mapped_column(String(40))
    response_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("exercise_responses.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
