"""Background worker (ARQ). Run with:  uv run python -m app.workers.main"""

import logging
import sys
import uuid
from typing import Any

from arq import cron, run_worker

import app.models  # noqa: F401  (registers every table for FK resolution)
from app.core.db import SessionLocal
from app.core.logging import configure_logging
from app.speech import service as speech
from app.speech.provider import get_speech_provider
from app.storage.audio import get_audio_store
from app.workers.queue import redis_settings


async def startup(ctx: dict[str, Any]) -> None:
    configure_logging()
    provider = get_speech_provider()
    provider._load()  # type: ignore[attr-defined]  # load model once, before the first job
    ctx["speech"] = provider
    logging.getLogger("app.worker").info("worker ready")


async def process_speech(ctx: dict[str, Any], asset_id: str) -> str | None:
    async with SessionLocal() as db:
        asset = await speech.process(db, uuid.UUID(asset_id), get_audio_store(), ctx["speech"])
        return asset.status if asset else None


async def sweep_stale_audio(ctx: dict[str, Any]) -> int:
    async with SessionLocal() as db:
        return await speech.sweep_stale(db, get_audio_store())


class WorkerSettings:
    functions = [process_speech]
    cron_jobs = [cron(sweep_stale_audio, minute=set(range(0, 60, 5)))]
    on_startup = startup
    redis_settings = redis_settings()
    max_jobs = 2
    job_timeout = 120
    max_tries = 1  # never re-run a job whose audio may already be deleted
    # asyncio signal handlers are unavailable on Windows.
    handle_signals = sys.platform != "win32"


if __name__ == "__main__":
    run_worker(WorkerSettings)  # type: ignore[arg-type]
