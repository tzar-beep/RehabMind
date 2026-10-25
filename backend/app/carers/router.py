"""What a carer sees and does. Activity and goals only: never scores, answers, transcripts
or anything the clinician records."""

import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import select

from app.auth.deps import CarerUser, DbDep
from app.carers.access import get_supported_patient
from app.carers.models import PatientCarer
from app.goals import service as goals
from app.goals.service import GoalOut
from app.patients.models import Patient
from app.sessions.router import PracticeActivity, activity_of
from app.users.models import User

router = APIRouter(prefix="/carer", tags=["carer"])

_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")


class SupportedPatient(BaseModel):
    id: str
    display_name: str
    relationship: str


class CarerSummary(BaseModel):
    patient: SupportedPatient
    activity: PracticeActivity
    goals: list[GoalOut]


@router.get("/patients", response_model=list[SupportedPatient])
async def my_patients(user: CarerUser, db: DbDep) -> list[SupportedPatient]:
    rows = await db.execute(
        select(Patient.id, User.display_name, PatientCarer.relationship)
        .join(PatientCarer, PatientCarer.patient_id == Patient.id)
        .join(User, User.id == Patient.user_id)
        .where(PatientCarer.user_id == user.id)
        .order_by(User.display_name)
    )
    return [SupportedPatient(id=str(i), display_name=n, relationship=r) for i, n, r in rows]


@router.get("/patients/{patient_id}", response_model=CarerSummary)
async def patient_summary(patient_id: uuid.UUID, user: CarerUser, db: DbDep) -> CarerSummary:
    patient = await get_supported_patient(db, user, patient_id)
    if patient is None:
        raise _NOT_FOUND
    name = await db.scalar(select(User.display_name).where(User.id == patient.user_id))
    relationship = await db.scalar(
        select(PatientCarer.relationship).where(
            PatientCarer.patient_id == patient.id, PatientCarer.user_id == user.id
        )
    )
    current = await goals.goals_of(db, patient.id, current=True)
    return CarerSummary(
        patient=SupportedPatient(
            id=str(patient.id), display_name=name or "", relationship=relationship or ""
        ),
        activity=await activity_of(db, patient.id),
        goals=await goals.with_progress(db, patient.id, current),
    )
