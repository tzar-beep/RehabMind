import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select, tuple_

from app.ai.models import AIGeneration
from app.ai.personalization import TASK
from app.auth.deps import ClinicianUser, DbDep
from app.exercises.models import Exercise, Stimulus
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
        .where(AIGeneration.patient_id == patient_id, AIGeneration.task == TASK)
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


class AIAttempt(BaseModel):
    attempt: int
    status: str  # accepted | rejected | error
    failed_stage: str | None
    reason_codes: list[str]
    latency_ms: int
    output: dict[str, Any] | None


class FinalExercise(BaseModel):
    id: str
    source: str  # ai | rule | fallback
    difficulty: int
    picture: str | None
    prompt: str


class AIRun(BaseModel):
    """All AI attempts for one exercise slot, and what the patient actually received."""

    session_id: str
    position: int | None
    created_at: datetime
    # ai_generated | ai_generated_after_retry | rule_based_used | no_exercise
    result: str
    provider: str
    model: str
    prompt_version: str
    constraint_version: int
    target_difficulty: int
    recent_outcomes: list[str]
    candidates: int
    selection_reason: str | None
    attempts: list[AIAttempt]
    final_exercise: FinalExercise | None


def _result(attempts: list[AIGeneration], final: Exercise | None) -> str:
    accepted = [a for a in attempts if a.status == "accepted"]
    if accepted:
        return "ai_generated" if accepted[0].attempt == 1 else "ai_generated_after_retry"
    return "rule_based_used" if final is not None else "no_exercise"


@router.get("/runs", response_model=list[AIRun])
async def list_runs(
    patient_id: uuid.UUID,
    user: ClinicianUser,
    db: DbDep,
    limit: int = Query(default=30, ge=1, le=100),
) -> list[AIRun]:
    """AI attempts grouped per exercise slot (session + position), newest first."""
    if await get_accessible_patient(db, user, patient_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")
    rows = (
        await db.execute(
            select(AIGeneration)
            .where(AIGeneration.patient_id == patient_id, AIGeneration.task == TASK)
            .order_by(AIGeneration.created_at.desc())
            .limit(limit * 3)  # at most MAX_ATTEMPTS (+ issuer) rows per slot
        )
    ).scalars()
    # One slot = one issue_next() call. Rows carry session + position; rows written before
    # `exercise_position` existed are grouped by transaction instead: all attempts and the
    # issued exercise share Postgres' transaction timestamp (created_at == issued_at).
    groups: dict[tuple, list[AIGeneration]] = {}
    for g in rows:
        key = (
            ("pos", g.session_id, g.exercise_position)
            if g.exercise_position is not None
            else ("tx", g.session_id, g.created_at)
        )
        groups.setdefault(key, []).append(g)
    keys = list(groups)[:limit]

    finals: dict[tuple, tuple[Exercise, Stimulus | None]] = {}
    by_pos = [(sid, pos) for kind, sid, pos in keys if kind == "pos"]
    by_tx = [(sid, ts) for kind, sid, ts in keys if kind == "tx"]
    base = select(Exercise, Stimulus).join(
        Stimulus, Stimulus.id == Exercise.stimulus_id, isouter=True
    )
    if by_pos:
        for ex, stim in (
            await db.execute(base.where(tuple_(Exercise.session_id, Exercise.position).in_(by_pos)))
        ).all():
            finals[("pos", ex.session_id, ex.position)] = (ex, stim)
    if by_tx:
        for ex, stim in (
            await db.execute(base.where(tuple_(Exercise.session_id, Exercise.issued_at).in_(by_tx)))
        ).all():
            finals[("tx", ex.session_id, ex.issued_at)] = (ex, stim)

    runs = []
    for key in keys:
        attempts = sorted(groups[key], key=lambda a: a.attempt)
        first = attempts[0]
        final, stim = finals.get(key, (None, None))
        accepted = next((a for a in attempts if a.status == "accepted"), None)
        runs.append(
            AIRun(
                session_id=str(first.session_id),
                position=first.exercise_position or (final.position if final else None),
                created_at=first.created_at,
                result=_result(attempts, final),
                provider=first.provider,
                model=attempts[-1].model,
                prompt_version=first.prompt_version,
                constraint_version=first.constraint_version,
                target_difficulty=first.input_snapshot["target_difficulty"],
                recent_outcomes=first.input_snapshot["recent_outcomes"],
                candidates=len(first.input_snapshot["candidates"]),
                selection_reason=(accepted.parsed_output or {}).get("rationale")
                if accepted
                else None,
                attempts=[
                    AIAttempt(
                        attempt=a.attempt,
                        status=a.status,
                        failed_stage=a.failed_stage,
                        reason_codes=a.reason_codes,
                        latency_ms=a.latency_ms,
                        output=a.parsed_output,
                    )
                    for a in attempts
                ],
                final_exercise=FinalExercise(
                    id=str(final.id),
                    source=final.source,
                    difficulty=final.difficulty,
                    picture=stim.slug if stim else None,
                    prompt=final.content["prompt"],
                )
                if final
                else None,
            )
        )
    return runs
