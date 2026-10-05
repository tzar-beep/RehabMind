import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import func, select

from app.audit import service as audit
from app.auth.deps import ClinicianUser, DbDep
from app.clinical.models import ConstraintSet
from app.clinical.service import (
    ConstraintSetIn,
    ConstraintSetOut,
    create_version,
    latest_constraints,
)
from app.clinicians.schemas import ConstraintVersion
from app.exercises.models import Stimulus
from app.exercises.types import (
    IMPLEMENTED_TYPES,
    MAX_DIFFICULTY,
    MIN_DIFFICULTY,
    ExerciseType,
    ResponseMode,
)
from app.patients.access import get_accessible_patient
from app.users.models import User

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


@router.get("/versions", response_model=list[ConstraintVersion])
async def constraint_history(patient_id: uuid.UUID, user: ClinicianUser, db: DbDep):
    """Every version, newest first. History is read-only; versions are never edited."""
    if await get_accessible_patient(db, user, patient_id) is None:
        raise _NOT_FOUND
    rows = (
        await db.execute(
            select(ConstraintSet, User.display_name)
            .join(User, User.id == ConstraintSet.created_by_user_id)
            .where(ConstraintSet.patient_id == patient_id)
            .order_by(ConstraintSet.version.desc())
        )
    ).all()
    return [
        ConstraintVersion(
            **ConstraintSetOut.of(cs).model_dump(mode="json"),
            is_active=i == 0,
            created_at=cs.created_at,
            created_by=author,
        )
        for i, (cs, author) in enumerate(rows)
    ]


options_router = APIRouter(prefix="/clinical", tags=["clinical"])


class ConstraintOptions(BaseModel):
    """Choices and limits for the constraint form, taken from the same sources the backend
    validates against (so the UI does not duplicate rules)."""

    exercise_types: list[dict[str, object]]
    response_modes: list[str]
    # category -> number of active pictures per difficulty level
    categories: dict[str, dict[int, int]]
    difficulty: tuple[int, int]
    max_exercises_per_session: tuple[int, int]
    progression_rule: tuple[int, int]


@options_router.get("/constraint-options", response_model=ConstraintOptions)
async def constraint_options(_: ClinicianUser, db: DbDep) -> ConstraintOptions:
    categories: dict[str, dict[int, int]] = {}
    for category, level, n in (
        await db.execute(
            select(Stimulus.category, Stimulus.difficulty, func.count())
            .where(Stimulus.is_active)
            .group_by(Stimulus.category, Stimulus.difficulty)
        )
    ).all():
        categories.setdefault(category, {})[level] = n
    return ConstraintOptions(
        exercise_types=[
            {"value": t.value, "available": t in IMPLEMENTED_TYPES} for t in ExerciseType
        ],
        response_modes=[m.value for m in ResponseMode],
        categories=dict(sorted(categories.items())),
        difficulty=(MIN_DIFFICULTY, MAX_DIFFICULTY),
        max_exercises_per_session=(1, 50),
        progression_rule=(1, 10),
    )
