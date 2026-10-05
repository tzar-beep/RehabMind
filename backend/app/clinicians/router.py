from fastapi import APIRouter

from app.auth.deps import ClinicianUser, DbDep
from app.patients.access import accessible_patients
from app.patients.models import Patient
from app.patients.router import PatientOut

router = APIRouter(prefix="/clinicians", tags=["clinicians"])


@router.get("/me/patients", response_model=list[PatientOut])
async def my_patients(user: ClinicianUser, db: DbDep) -> list[PatientOut]:
    rows = await db.execute(accessible_patients(user).order_by(Patient.created_at))
    return [PatientOut.of(p) for p in rows.scalars()]
