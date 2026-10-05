import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.audit.models import AuditLog
from app.core.logging import request_id_var


async def record(
    db: AsyncSession,
    action: str,
    outcome: str,
    *,
    actor_user_id: uuid.UUID | None = None,
    target_type: str | None = None,
    target_id: object | None = None,
    details: dict[str, Any] | None = None,
    commit: bool = True,
) -> None:
    """Write an audit entry. `details` must never contain passwords, tokens or PII."""
    db.add(
        AuditLog(
            action=action,
            outcome=outcome,
            actor_user_id=actor_user_id,
            target_type=target_type,
            target_id=str(target_id) if target_id is not None else None,
            request_id=request_id_var.get(),
            details=details or {},
        )
    )
    if commit:
        await db.commit()
