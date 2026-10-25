import uuid
from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.auth.deps import ClinicianUser, DbDep, PatientUser
from app.patients.access import accessible_patients, get_accessible_patient
from app.wellbeing.models import MoodCheckin

patient_router = APIRouter(prefix="/practice/mood", tags=["wellbeing"])
clinician_router = APIRouter(prefix="/patients/{patient_id}/moods", tags=["wellbeing"])

Mood = Literal["good", "okay", "low"]
DAYS = 14


class MoodIn(BaseModel):
    mood: Mood
    # The patient's own calendar day (their device's date), so "today" is theirs.
    day: date


class MoodDay(BaseModel):
    day: date
    mood: Mood


async def _patient(user: PatientUser, db: DbDep):
    patient = (await db.execute(accessible_patients(user))).scalar_one_or_none()
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient profile not found.")
    return patient


@patient_router.get("", response_model=MoodDay | None)
async def todays_mood(day: date, user: PatientUser, db: DbDep) -> MoodDay | None:
    patient = await _patient(user, db)
    row = await db.scalar(
        select(MoodCheckin).where(MoodCheckin.patient_id == patient.id, MoodCheckin.day == day)
    )
    return MoodDay(day=row.day, mood=row.mood) if row else None


@patient_router.put("", response_model=MoodDay)
async def set_mood(body: MoodIn, user: PatientUser, db: DbDep) -> MoodDay:
    """One check-in a day; tapping again the same day changes it."""
    if abs((body.day - date.today()).days) > 1:  # a device date, within a day of ours
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "That is not today.")
    patient = await _patient(user, db)
    row = await db.scalar(
        select(MoodCheckin).where(MoodCheckin.patient_id == patient.id, MoodCheckin.day == body.day)
    )
    if row is None:
        db.add(MoodCheckin(patient_id=patient.id, day=body.day, mood=body.mood))
    else:
        row.mood = body.mood
    await db.commit()
    return MoodDay(day=body.day, mood=body.mood)


@clinician_router.get("", response_model=list[MoodDay])
async def recent_moods(patient_id: uuid.UUID, user: ClinicianUser, db: DbDep) -> list[MoodDay]:
    """The last two weeks of check-ins, oldest first."""
    if await get_accessible_patient(db, user, patient_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")
    rows = await db.execute(
        select(MoodCheckin.day, MoodCheckin.mood)
        .where(
            MoodCheckin.patient_id == patient_id,
            MoodCheckin.day >= date.today() - timedelta(days=DAYS),
        )
        .order_by(MoodCheckin.day)
    )
    return [MoodDay(day=d, mood=m) for d, m in rows.all()]
