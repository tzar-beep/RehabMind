"""Curated stimulus library. `stimuli_catalog.json` is the reviewed source of truth."""

import json
from pathlib import Path

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.exercises.models import Stimulus
from app.exercises.types import ExerciseType

CATALOG_PATH = Path(__file__).with_name("stimuli_catalog.json")


def load_catalog() -> dict:
    return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))


async def sync_stimuli(db: AsyncSession) -> int:
    """Upsert catalog entries; deactivate stimuli no longer in the catalog. Idempotent."""
    catalog = load_catalog()
    existing = {s.slug: s for s in (await db.execute(select(Stimulus))).scalars()}
    slugs = set()
    entries = [
        {
            "slug": e["slug"],
            "target": e["target"],
            "accepted_answers": e["accepted_answers"],
            "category": e["category"],
            "difficulty": e["difficulty"],
            "image_path": f"/stimuli/{e['slug']}.svg",
            "kind": "icon",
            "exercise_types": [ExerciseType.PICTURE_NAMING.value],
            "task": {},
            "license": catalog["source"]["license"],
            "attribution": catalog["source"]["name"],
            "source_url": catalog["source"]["url"],
        }
        for e in catalog["stimuli"]
    ] + [
        {
            "slug": p["slug"],
            "target": p["target"],
            "accepted_answers": p["accepted_answers"],
            "category": p["category"],
            "difficulty": p["difficulty"],
            "image_path": p["image_path"],
            "kind": "photo",
            "exercise_types": p["exercise_types"],
            "task": {k: p[k] for k in ("description", "sentence") if k in p},
            "license": p["license"],
            "attribution": p["attribution"][:200],
            "source_url": p["source_url"],
        }
        for p in catalog.get("photos", [])
    ]
    for entry in entries:
        slug = entry.pop("slug")
        slugs.add(slug)
        values = {**entry, "catalog_version": catalog["version"], "is_active": True}
        if (stim := existing.get(slug)) is None:
            db.add(Stimulus(slug=slug, **values))
        else:
            for k, v in values.items():
                setattr(stim, k, v)
    if stale := set(existing) - slugs:
        await db.execute(update(Stimulus).where(Stimulus.slug.in_(stale)).values(is_active=False))
    await db.commit()
    return len(slugs)
