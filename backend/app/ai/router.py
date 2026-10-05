import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select

from app.ai.models import AIGeneration
from app.auth.deps import ClinicianUser, DbDep
from app.patients.access import get_accessible_patient

router = APIRouter(prefix="/patients/{patient_id}/ai-generations", tags=["ai"])


class AIGenerationOut(BaseModel):
    """Explainable metadata for clinicians: inputs, verdict and reason codes — no model
    reasoning (none is requested or stored)."""

    id: str
    created_at: datetime
    attempt: int
    status: str
    failed_stage: str | None
    reason_codes: list[str]
    provider: str
    model: str
    prompt_version: str
    constraint_version: int
    exercise_id: str | None
    target_difficulty: int
    recent_outcomes: list[str]
    output: dict[str, Any] | None


@router.get("", response_model=list[AIGenerationOut])
async def list_generations(
    patient_id: uuid.UUID,
    user: ClinicianUser,
    db: DbDep,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[AIGenerationOut]:
    if await get_accessible_patient(db, user, patient_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")
    rows = await db.execute(
        select(AIGeneration)
        .where(AIGeneration.patient_id == patient_id)
        .order_by(AIGeneration.created_at.desc(), AIGeneration.attempt.desc())
        .limit(limit)
    )
    return [
        AIGenerationOut(
            id=str(g.id),
            created_at=g.created_at,
            attempt=g.attempt,
            status=g.status,
            failed_stage=g.failed_stage,
            reason_codes=g.reason_codes,
            provider=g.provider,
            model=g.model,
            prompt_version=g.prompt_version,
            constraint_version=g.constraint_version,
            exercise_id=str(g.exercise_id) if g.exercise_id else None,
            target_difficulty=g.input_snapshot["target_difficulty"],
            recent_outcomes=g.input_snapshot["recent_outcomes"],
            output=g.parsed_output,
        )
        for g in rows.scalars()
    ]
