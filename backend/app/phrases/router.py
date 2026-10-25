"""Everyday phrases (script training): short real-life conversations practised line by
line, hear it, say it together, say it alone. Practising whole scripts carries over into
everyday talk better than single words, and practice at home is self-reported, not
scored."""

import json
import uuid
from datetime import UTC, datetime, timedelta
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.auth.deps import ClinicianUser, DbDep, PatientUser
from app.patients.access import accessible_patients, get_accessible_patient
from app.phrases.models import ScriptPractice
from app.users.models import User

patient_router = APIRouter(prefix="/practice/phrases", tags=["phrases"])
clinician_router = APIRouter(prefix="/patients/{patient_id}/phrases", tags=["phrases"])

RECENT = timedelta(days=14)


@lru_cache
def scripts() -> dict[str, dict]:
    data = json.loads(Path(__file__).with_name("scripts.json").read_text(encoding="utf-8"))
    return {s["id"]: s for s in data["scripts"]}


class Script(BaseModel):
    id: str
    title: str
    icon: str
    lines: list[str]
    times_practised: int
    last_practised: datetime | None


class Done(BaseModel):
    lines_said: int = Field(ge=0, le=20)


class ScriptSummary(BaseModel):
    id: str
    title: str
    times_recent: int  # last 14 days
    times_total: int
    lines_said_share: float | None  # of lines in recent runs, by the patient's own report
    last_practised: datetime | None


async def _stats(db, patient_id: uuid.UUID) -> dict[str, tuple[int, int, int, int, datetime]]:
    recent = datetime.now(UTC) - RECENT
    rows = await db.execute(
        select(
            ScriptPractice.script_id,
            func.count(),
            func.count().filter(ScriptPractice.created_at >= recent),
            func.coalesce(
                func.sum(ScriptPractice.lines_said).filter(ScriptPractice.created_at >= recent), 0
            ),
            func.coalesce(
                func.sum(ScriptPractice.lines_total).filter(ScriptPractice.created_at >= recent), 0
            ),
            func.max(ScriptPractice.created_at),
        )
        .where(ScriptPractice.patient_id == patient_id)
        .group_by(ScriptPractice.script_id)
    )
    return {sid: (total, rec, said, lines, last) for sid, total, rec, said, lines, last in rows}


async def _patient(user: PatientUser, db: DbDep):
    patient = (await db.execute(accessible_patients(user))).scalar_one_or_none()
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient profile not found.")
    return patient


@patient_router.get("", response_model=list[Script])
async def my_scripts(user: PatientUser, db: DbDep) -> list[Script]:
    patient = await _patient(user, db)
    name = await db.scalar(select(User.display_name).where(User.id == patient.user_id))
    stats = await _stats(db, patient.id)
    return [
        Script(
            id=s["id"],
            title=s["title"],
            icon=s["icon"],
            lines=[line.replace("{name}", name or "") for line in s["lines"]],
            times_practised=stats.get(s["id"], (0,))[0],
            last_practised=stats[s["id"]][4] if s["id"] in stats else None,
        )
        for s in scripts().values()
    ]


@patient_router.post("/{script_id}/done", status_code=status.HTTP_201_CREATED)
async def practised(script_id: str, body: Done, user: PatientUser, db: DbDep) -> dict:
    script = scripts().get(script_id)
    if script is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Script not found.")
    total = len(script["lines"])
    patient = await _patient(user, db)
    db.add(
        ScriptPractice(
            patient_id=patient.id,
            script_id=script_id,
            lines_said=min(body.lines_said, total),
            lines_total=total,
        )
    )
    await db.commit()
    return {"ok": True}


@clinician_router.get("", response_model=list[ScriptSummary])
async def patient_scripts(
    patient_id: uuid.UUID, user: ClinicianUser, db: DbDep
) -> list[ScriptSummary]:
    if await get_accessible_patient(db, user, patient_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")
    stats = await _stats(db, patient_id)
    out = []
    for s in scripts().values():
        total, recent, said, lines, last = stats.get(s["id"], (0, 0, 0, 0, None))
        out.append(
            ScriptSummary(
                id=s["id"],
                title=s["title"],
                times_recent=recent,
                times_total=total,
                lines_said_share=round(said / lines, 2) if lines else None,
                last_practised=last,
            )
        )
    return out
