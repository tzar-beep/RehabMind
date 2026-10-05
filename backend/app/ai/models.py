import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Integer, SmallInteger, String, Text, func
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class AIGeneration(Base):
    """Audit record for every AI call: what was asked, what came back, and the verdict.

    Append-only for the runtime role. Contains no chain-of-thought (none is requested) and
    no direct identifiers in `input_snapshot`.
    """

    __tablename__ = "ai_generations"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("patients.id", ondelete="CASCADE"), index=True
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("practice_sessions.id", ondelete="CASCADE"), index=True
    )
    exercise_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("exercises.id"))
    task: Mapped[str] = mapped_column(String(60))
    attempt: Mapped[int] = mapped_column(SmallInteger)
    provider: Mapped[str] = mapped_column(String(40))
    model: Mapped[str] = mapped_column(String(80))
    model_version: Mapped[str | None] = mapped_column(String(40))
    prompt_version: Mapped[str] = mapped_column(String(40))
    constraint_set_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clinical_constraint_sets.id"))
    constraint_version: Mapped[int]
    input_snapshot: Mapped[dict[str, Any]] = mapped_column(JSONB)
    raw_output: Mapped[str | None] = mapped_column(Text)
    parsed_output: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    # accepted | rejected | error
    status: Mapped[str] = mapped_column(String(16))
    # provider | schema | clinical | safety | issuer
    failed_stage: Mapped[str | None] = mapped_column(String(16))
    reason_codes: Mapped[list[str]] = mapped_column(ARRAY(String(60)), default=list)
    latency_ms: Mapped[int] = mapped_column(Integer)
