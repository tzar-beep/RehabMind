import uuid

from fastapi import APIRouter, HTTPException, status

from app.audit import service as audit
from app.auth.deps import ClinicianUser, DbDep
from app.clinical.service import (
    ConstraintSetIn,
    ConstraintSetOut,
    create_version,
    latest_constraints,
)
from app.patients.access import get_accessible_patient

router = APIRouter(prefix="/patients/{patient_id}/constraints", tags=["clinical"])

_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")


@router.get("", response_model=ConstraintSetOut)
async def get_constraints(patient_id: uuid.UUID, user: ClinicianUser, db: DbDep):
    if await get_accessible_patient(db, user, patient_id) is None:
        raise _NOT_FOUND
    cs = await latest_constraints(db, patient_id)
    if cs is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No constraints set for this patient.")
    return ConstraintSetOut.of(cs)


@router.post("", response_model=ConstraintSetOut, status_code=status.HTTP_201_CREATED)
async def set_constraints(
    patient_id: uuid.UUID, body: ConstraintSetIn, user: ClinicianUser, db: DbDep
):
    """Create a new constraint version. Applies from the next exercise issued."""
    if await get_accessible_patient(db, user, patient_id) is None:
        await audit.record(
            db,
            "constraints.create",
            "denied",
            actor_user_id=user.id,
            target_type="patient",
            target_id=patient_id,
        )
        raise _NOT_FOUND
    cs = await create_version(db, patient_id, body, user.id)
    await audit.record(
        db,
        "constraints.create",
        "success",
        actor_user_id=user.id,
        target_type="patient",
        target_id=patient_id,
        details={"version": cs.version, "min": cs.min_difficulty, "max": cs.max_difficulty},
        commit=False,
    )
    await db.commit()
    return ConstraintSetOut.of(cs)
