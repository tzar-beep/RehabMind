"""Curated stimulus library. `stimuli_catalog.json` is the reviewed source of truth."""

import json
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.exercises.models import Stimulus

CATALOG_PATH = Path(__file__).with_name("stimuli_catalog.json")


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


async def sync_stimuli(db: AsyncSession) -> int:
    """Upsert catalog entries; deactivate stimuli no longer in the catalog. Idempotent."""
    catalog = load_catalog()
    existing = {s.slug: s for s in (await db.execute(select(Stimulus))).scalars()}
    slugs = set()
    for entry in catalog["stimuli"]:
        slugs.add(entry["slug"])
        values = {
            "target": entry["target"],
            "accepted_answers": entry["accepted_answers"],
            "category": entry["category"],
            "difficulty": entry["difficulty"],
            "image_path": f"/stimuli/{entry['slug']}.svg",
            "license": catalog["source"]["license"],
            "catalog_version": catalog["version"],
            "is_active": True,
        }
        if (stim := existing.get(entry["slug"])) is None:
            db.add(Stimulus(slug=entry["slug"], **values))
        else:
            for k, v in values.items():
                setattr(stim, k, v)
    if stale := set(existing) - slugs:
        await db.execute(update(Stimulus).where(Stimulus.slug.in_(stale)).values(is_active=False))
    await db.commit()
    return len(slugs)
