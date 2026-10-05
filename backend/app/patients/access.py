"""The single authorization point for reading patient records.

Every query for patient-owned data must be scoped through `accessible_patients`, so the
access rule lives in SQL rather than in scattered `if` checks:
  - a patient sees only their own record
  - a clinician sees only patients assigned to them
  - admins have no clinical access
"""

import uuid

from sqlalchemy import Select, exists, false, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.deps import CurrentUser
from app.clinicians.models import Clinician, PatientClinician
from app.patients.models import Patient
from app.users.models import Role


def accessible_patients(actor: CurrentUser) -> Select[tuple[Patient]]:
    stmt = select(Patient)
    if actor.role is Role.PATIENT:
        return stmt.where(Patient.user_id == actor.id)
    if actor.role is Role.CLINICIAN:
        assigned = (
            select(PatientClinician.patient_id)
            .join(Clinician, Clinician.id == PatientClinician.clinician_id)
            .where(PatientClinician.patient_id == Patient.id, Clinician.user_id == actor.id)
        )
        return stmt.where(exists(assigned))
    return stmt.where(false())


async def get_accessible_patient(
    db: AsyncSession, actor: CurrentUser, patient_id: uuid.UUID
) -> Patient | None:
    stmt = accessible_patients(actor).where(Patient.id == patient_id)
    return (await db.execute(stmt)).scalar_one_or_none()
