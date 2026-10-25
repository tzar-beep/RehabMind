"""Which patients a carer supports. Deliberately separate from `accessible_patients`
(app/patients/access.py), which gates clinical data: carers are never in that rule."""

import uuid

from sqlalchemy import Select, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.carers.models import PatientCarer
from app.patients.models import Patient


def supported_patients(carer: CurrentUser) -> Select[tuple[Patient]]:
    link = select(PatientCarer.patient_id).where(
        PatientCarer.patient_id == Patient.id, PatientCarer.user_id == carer.id
    )
    return select(Patient).where(exists(link))


async def get_supported_patient(
    db: AsyncSession, carer: CurrentUser, patient_id: uuid.UUID
) -> Patient | None:
    stmt = supported_patients(carer).where(Patient.id == patient_id)
    return (await db.execute(stmt)).scalar_one_or_none()
