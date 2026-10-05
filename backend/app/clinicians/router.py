from fastapi import APIRouter

from app.auth.deps import ClinicianUser, DbDep
from app.clinicians import insights
from app.clinicians.schemas import PatientListItem
from app.patients.access import accessible_patients
from app.patients.models import Patient

router = APIRouter(prefix="/clinicians", tags=["clinicians"])


@router.get("/me/patients", response_model=list[PatientListItem])
async def my_patients(user: ClinicianUser, db: DbDep) -> list[PatientListItem]:
    """Assigned patients with bounded, factual activity summaries."""
    rows = await db.execute(accessible_patients(user).order_by(Patient.created_at))
    return await insights.patient_list(db, list(rows.scalars()))
