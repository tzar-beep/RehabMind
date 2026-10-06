"""Generate → validate → retry → log, for feedback and summaries.

The same bounded policy as exercise personalization: at most MAX_ATTEMPTS calls, every
attempt written to `ai_generations`, and `None` when nothing valid came back (the caller then
uses its non-AI fallback). Never a loop the model controls.
"""

import asyncio
import time
import uuid
from collections.abc import Callable
from typing import Any

from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.models import AIGeneration
from app.ai.provider import AIProvider, AIProviderError, GenerationRequest
from app.core.config import get_settings
from app.validation.exercise import Verdict

MAX_ATTEMPTS = 2
RAW_OUTPUT_LIMIT = 4000

Validator = Callable[[str], tuple[Verdict, BaseModel | None]]


async def generate_validated(
    db: AsyncSession,
    provider: AIProvider,
    request: GenerationRequest,
    validate: Validator,
    *,
    patient_id: uuid.UUID,
    constraint_set_id: uuid.UUID,
    constraint_version: int,
    session_id: uuid.UUID | None = None,
    exercise_id: uuid.UUID | None = None,
    exercise_position: int | None = None,
) -> tuple[Any, AIGeneration | None]:
    timeout = get_settings().ai_timeout_s
    for attempt in range(1, MAX_ATTEMPTS + 1):
        row = AIGeneration(
            patient_id=patient_id,
            session_id=session_id,
            exercise_id=exercise_id,
            exercise_position=exercise_position,
            task=request.task,
            attempt=attempt,
            provider=getattr(provider, "name", "unknown"),
            model="unknown",
            prompt_version=request.prompt_version,
            constraint_set_id=constraint_set_id,
            constraint_version=constraint_version,
            input_snapshot=request.input,
            reason_codes=[],
        )
        started = time.perf_counter()
        try:
            result = await asyncio.wait_for(provider.generate(request), timeout)
        except (AIProviderError, TimeoutError) as e:
            row.latency_ms = int((time.perf_counter() - started) * 1000)
            row.status, row.failed_stage = "error", "provider"
            row.reason_codes = ["timeout" if isinstance(e, TimeoutError) else "provider_error"]
            db.add(row)
            continue
        row.latency_ms = int((time.perf_counter() - started) * 1000)
        row.provider, row.model, row.model_version = (
            result.provider,
            result.model,
            result.model_version,
        )
        row.usage = result.usage or None
        row.raw_output = result.raw_output[:RAW_OUTPUT_LIMIT]
        verdict, out = validate(result.raw_output)
        if out is not None:
            row.parsed_output = out.model_dump(mode="json")
        if verdict.ok and out is not None:
            row.status = "accepted"
            db.add(row)
            return out, row
        row.status, row.failed_stage, row.reason_codes = "rejected", verdict.stage, verdict.reasons
        db.add(row)
    return None, None
