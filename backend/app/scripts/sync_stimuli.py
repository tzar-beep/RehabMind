"""Sync the curated stimulus catalog into the database (safe in every environment).

Usage:  uv run python -m app.scripts.sync_stimuli
"""

import asyncio

from app.core.db import SessionLocal
from app.exercises.catalog import sync_stimuli


async def _main() -> None:
    async with SessionLocal() as db:
        print(f"synced {await sync_stimuli(db)} stimuli")


if __name__ == "__main__":
    asyncio.run(_main())
