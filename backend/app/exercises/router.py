"""Public photo credits: who made each practice picture, and under which licence."""

from functools import cache

from fastapi import APIRouter
from pydantic import BaseModel

from app.exercises.catalog import load_catalog

router = APIRouter(prefix="/stimuli", tags=["stimuli"])


class PhotoCredit(BaseModel):
    image: str
    word: str
    source: str
    attribution: str
    license: str
    license_url: str | None
    source_url: str
    # BOSS photos: share of people who gave the picture its most common name (0-1).
    name_agreement: float | None = None


@cache
def _credits() -> list[PhotoCredit]:
    return [
        PhotoCredit(
            image=p["image_path"],
            word=p["target"],
            source=p["source"],
            attribution=p["attribution"],
            license=p["license"],
            license_url=p.get("license_url"),
            source_url=p["source_url"],
            name_agreement=(p.get("norms") or {}).get("name_agreement"),
        )
        for p in load_catalog()["photos"]
    ]


@router.get("/credits", response_model=list[PhotoCredit])
async def photo_credits() -> list[PhotoCredit]:
    """No sign-in needed: the licences require the credit to be visible where photos are used."""
    return _credits()
