import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from app.audit import service as audit
from app.auth.deps import CurrentUserDep, DbDep, PatientUser
from app.patients.access import accessible_patients, get_accessible_patient
from app.patients.models import Patient

router = APIRouter(prefix="/patients", tags=["patients"])


class PatientOut(BaseModel):
    id: str
    display_name: str

    @classmethod
    def of(cls, p: Patient) -> "PatientOut":
        return cls(id=str(p.id), display_name=p.user.display_name)


@router.get("/me", response_model=PatientOut)
async def my_profile(user: PatientUser, db: DbDep) -> PatientOut:
    patient = (await db.execute(accessible_patients(user))).scalar_one_or_none()
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient profile not found.")
    return PatientOut.of(patient)


@router.get("/{patient_id}", response_model=PatientOut)
async def get_patient(patient_id: uuid.UUID, user: CurrentUserDep, db: DbDep) -> PatientOut:
    patient = await get_accessible_patient(db, user, patient_id)
    if patient is None:
        # 404 (not 403) so inaccessible records are indistinguishable from missing ones.
        await audit.record(
            db,
            "patient.read",
            "denied",
            actor_user_id=user.id,
            target_type="patient",
            target_id=patient_id,
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")
    return PatientOut.of(patient)
