"""Clinician-facing GenAI endpoints: provider status, progress summaries (use case 3) and the
development-only AI pipeline view used to demonstrate the whole flow step by step.

Every patient-scoped route resolves the patient through `get_accessible_patient` (404 when
not assigned), like all other clinician views.
"""

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy import select

from app.ai import feedback as ai_feedback
from app.ai import personalization, summary
from app.ai.models import AIGeneration
from app.ai.ollama import OllamaAIProvider
from app.ai.prompts import (
    EXERCISE_PROMPT_VERSION,
    FEEDBACK_PROMPT_VERSION,
    exercise_prompts,
    feedback_prompts,
)
from app.ai.provider import get_ai_provider
from app.ai.schemas import SummaryOutput
from app.auth.deps import ClinicianUser, DbDep
from app.clinical.service import latest_constraints
from app.core.config import get_settings
from app.exercises.models import Exercise, Stimulus
from app.exercises.types import OBJECTIVE_LABELS, OBJECTIVES
from app.patients.access import get_accessible_patient
from app.performance import ability
from app.sessions.models import ExerciseResponse

status_router = APIRouter(prefix="/ai", tags=["ai"])
router = APIRouter(prefix="/patients/{patient_id}", tags=["ai"])


class AIStatus(BaseModel):
    provider: str  # ollama | fake | none
    model: str | None
    generative: bool  # True only for a real LLM
    reachable: bool
    model_available: bool
    demo_view: bool


@status_router.get("/status", response_model=AIStatus)
async def ai_status(_: ClinicianUser) -> AIStatus:
    settings = get_settings()
    provider = get_ai_provider()
    if isinstance(provider, OllamaAIProvider):
        health = await provider.status()
        return AIStatus(
            provider="ollama",
            model=provider.model,
            generative=True,
            reachable=health["reachable"],
            model_available=health["model_available"],
            demo_view=settings.ai_demo_view,
        )
    return AIStatus(
        provider=settings.ai_provider,
        model=getattr(provider, "model", None),
        generative=False,
        reachable=provider is not None,
        model_available=provider is not None,
        demo_view=settings.ai_demo_view,
    )


async def _patient(db: DbDep, user: ClinicianUser, patient_id: uuid.UUID):
    patient = await get_accessible_patient(db, user, patient_id)
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")
    return patient


# ---------- use case 3: progress summary ----------


class ProgressSummaryOut(BaseModel):
    summary: str
    strengths: list[str]
    focus_areas: list[str]
    source: str  # ai | rules
    provider: str | None
    model: str | None
    prompt_version: str | None
    created_at: datetime | None
    figures: dict[str, Any]


def _summary_out(out, row: AIGeneration | None, figures: dict[str, Any]) -> ProgressSummaryOut:
    return ProgressSummaryOut(
        summary=out.summary,
        strengths=out.strengths,
        focus_areas=out.focus_areas,
        source="ai" if row else "rules",
        provider=row.provider if row else None,
        model=row.model if row else None,
        prompt_version=row.prompt_version if row else None,
        created_at=row.created_at if row else None,
        figures=figures,
    )


@router.post("/progress-summary", response_model=ProgressSummaryOut)
async def create_progress_summary(
    patient_id: uuid.UUID, user: ClinicianUser, db: DbDep
) -> ProgressSummaryOut:
    await _patient(db, user, patient_id)
    cs = await latest_constraints(db, patient_id)
    if cs is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Set practice limits first.")
    out, row, figures = await summary.summarize(db, get_ai_provider(), patient_id, cs)
    if row is not None:
        await db.refresh(row)
    return _summary_out(out, row, figures)


@router.get("/progress-summary", response_model=ProgressSummaryOut | None)
async def latest_progress_summary(
    patient_id: uuid.UUID, user: ClinicianUser, db: DbDep
) -> ProgressSummaryOut | None:
    await _patient(db, user, patient_id)
    row = await summary.latest(db, patient_id)
    if row is None:
        return None
    out = SummaryOutput.model_validate(row.parsed_output)
    return _summary_out(out, row, row.input_snapshot)


# ---------- development-only demonstration view ----------


class PipelineAttempt(BaseModel):
    attempt: int
    status: str
    failed_stage: str | None
    reason_codes: list[str]
    latency_ms: int
    provider: str
    model: str
    raw_output: str | None
    usage: dict[str, Any] | None


class PipelineGeneration(BaseModel):
    task: str
    prompt_version: str
    context: dict[str, Any]
    system_prompt: str | None
    user_prompt: str | None
    attempts: list[PipelineAttempt]
    output: dict[str, Any] | None


class PipelineTrace(BaseModel):
    position: int
    issued_at: datetime
    objective: str
    objective_label: str
    exercise_type: str
    difficulty: int
    source: str  # ai | rule | fallback
    picture: str | None
    image_url: str | None
    shown: dict[str, Any]  # prompt, cues and word bank the patient saw
    generation: PipelineGeneration | None
    response: dict[str, Any] | None
    feedback: PipelineGeneration | None


class PipelineOut(BaseModel):
    status: AIStatus
    abilities: dict[str, dict[str, Any]]
    traces: list[PipelineTrace]


def _generation(rows: list[AIGeneration]) -> PipelineGeneration | None:
    if not rows:
        return None
    rows = sorted(rows, key=lambda g: (g.created_at, g.attempt))
    first = rows[0]
    system = user = None
    if first.prompt_version == EXERCISE_PROMPT_VERSION:
        system, user = exercise_prompts(first.input_snapshot)
    elif first.prompt_version == FEEDBACK_PROMPT_VERSION:
        system, user = feedback_prompts(first.input_snapshot)
    accepted = next((g for g in rows if g.status == "accepted"), None)
    return PipelineGeneration(
        task=first.task,
        prompt_version=first.prompt_version,
        context=first.input_snapshot,
        system_prompt=system,
        user_prompt=user,
        attempts=[
            PipelineAttempt(
                attempt=g.attempt,
                status=g.status,
                failed_stage=g.failed_stage,
                reason_codes=g.reason_codes,
                latency_ms=g.latency_ms,
                provider=g.provider,
                model=g.model,
                raw_output=g.raw_output,
                usage=g.usage,
            )
            for g in rows
        ],
        output=accepted.parsed_output if accepted else None,
    )


@router.get("/ai-pipeline", response_model=PipelineOut)
async def ai_pipeline(
    patient_id: uuid.UUID,
    user: ClinicianUser,
    db: DbDep,
    limit: int = Query(default=8, ge=1, le=30),
) -> PipelineOut:
    """Step-by-step trace of the latest exercises (development demonstrations only)."""
    if not get_settings().ai_demo_view:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found.")
    await _patient(db, user, patient_id)
    rows = (
        await db.execute(
            select(Exercise, Stimulus, ExerciseResponse)
            .join(Stimulus, Stimulus.id == Exercise.stimulus_id, isouter=True)
            .join(ExerciseResponse, ExerciseResponse.exercise_id == Exercise.id, isouter=True)
            .where(Exercise.patient_id == patient_id)
            .order_by(Exercise.issued_at.desc())
            .limit(limit)
        )
    ).all()
    slots = {(ex.session_id, ex.position) for ex, _, _ in rows}
    gens = (
        await db.execute(
            select(AIGeneration).where(
                AIGeneration.patient_id == patient_id,
                AIGeneration.session_id.in_({s for s, _ in slots} or {uuid.uuid4()}),
            )
        )
    ).scalars()
    by_slot: dict[tuple, list[AIGeneration]] = {}
    for g in gens:
        by_slot.setdefault((g.task, g.session_id, g.exercise_position), []).append(g)

    traces = []
    for ex, stim, resp in rows:
        objective = OBJECTIVES.get(ex.exercise_type)
        traces.append(
            PipelineTrace(
                position=ex.position,
                issued_at=ex.issued_at,
                objective=objective.value if objective else "",
                objective_label=OBJECTIVE_LABELS[objective] if objective else "",
                exercise_type=ex.exercise_type,
                difficulty=ex.difficulty,
                source=ex.source,
                picture=stim.slug if stim else None,
                image_url=ex.content.get("image_url"),
                shown={
                    "prompt": ex.content.get("prompt"),
                    "cues": ex.content.get("cues", []),
                    "words": ex.content.get("words"),
                },
                generation=_generation(
                    by_slot.get((personalization.TASK, ex.session_id, ex.position), [])
                ),
                response={
                    "text": resp.text,
                    "mode": resp.mode,
                    "outcome": resp.outcome,
                    "score": resp.score,
                    "match_type": resp.analysis.get("match_type"),
                    "concepts_matched": resp.analysis.get("concepts_matched"),
                    "concepts_missing": resp.analysis.get("concepts_missing"),
                    "hints_used": resp.analysis.get("hints_used"),
                }
                if resp
                else None,
                feedback=_generation(
                    by_slot.get((ai_feedback.TASK, ex.session_id, ex.position), [])
                ),
            )
        )
    estimates = await ability.estimates(db, patient_id)
    return PipelineOut(
        status=await ai_status(user),
        abilities={k: v.as_dict() for k, v in estimates.items()},
        traces=traces,
    )
