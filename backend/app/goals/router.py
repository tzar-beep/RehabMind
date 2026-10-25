import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import func, select

from app.audit import service as audit
from app.auth.deps import ClinicianUser, DbDep, PatientUser
from app.goals import service
from app.goals.models import TherapyGoal
from app.goals.service import GoalIn, GoalOut
from app.patients.access import accessible_patients, get_accessible_patient

router = APIRouter(prefix="/patients/{patient_id}/goals", tags=["goals"])
patient_router = APIRouter(prefix="/practice", tags=["goals"])

_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")


@router.get("", response_model=list[GoalOut])
async def list_goals(patient_id: uuid.UUID, user: ClinicianUser, db: DbDep) -> list[GoalOut]:
    """Every goal, newest first, with current progress."""
    if await get_accessible_patient(db, user, patient_id) is None:
        raise _NOT_FOUND
    goals = await service.goals_of(db, patient_id, current=False)
    return await service.with_progress(db, patient_id, goals)


@router.post("", response_model=GoalOut, status_code=status.HTTP_201_CREATED)
async def create_goal(
    patient_id: uuid.UUID, body: GoalIn, user: ClinicianUser, db: DbDep
) -> GoalOut:
    if await get_accessible_patient(db, user, patient_id) is None:
        raise _NOT_FOUND
    active = await db.scalar(
        select(func.count()).where(
            TherapyGoal.patient_id == patient_id, TherapyGoal.status == "active"
        )
    )
    if (active or 0) >= service.MAX_ACTIVE:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"A patient can have up to {service.MAX_ACTIVE} active goals. End one first.",
        )
    goal = TherapyGoal(patient_id=patient_id, created_by=user.id, **body.model_dump())
    db.add(goal)
    await db.flush()
    await audit.record(
        db,
        "goal.created",
        "success",
        actor_user_id=user.id,
        target_type="patient",
        target_id=patient_id,
        details={"goal_id": str(goal.id), "kind": goal.kind, "target": goal.target},
        commit=False,
    )
    await db.commit()
    await db.refresh(goal)
    return (await service.with_progress(db, patient_id, [goal]))[0]


@router.post("/{goal_id}/end", response_model=GoalOut)
async def end_goal(
    patient_id: uuid.UUID, goal_id: uuid.UUID, user: ClinicianUser, db: DbDep
) -> GoalOut:
    """Stop working on a goal (kept for the record, no longer shown to the patient)."""
    if await get_accessible_patient(db, user, patient_id) is None:
        raise _NOT_FOUND
    goal = await db.get(TherapyGoal, goal_id)
    if goal is None or goal.patient_id != patient_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Goal not found.")
    if goal.status != "ended":
        goal.status, goal.ended_at = "ended", datetime.now(UTC)
        await audit.record(
            db,
            "goal.ended",
            "success",
            actor_user_id=user.id,
            target_type="patient",
            target_id=patient_id,
            details={"goal_id": str(goal.id)},
            commit=False,
        )
        await db.commit()
    return (await service.with_progress(db, patient_id, [goal]))[0]


@patient_router.get("/goals", response_model=list[GoalOut])
async def my_goals(user: PatientUser, db: DbDep) -> list[GoalOut]:
    """The patient's current goals (active, or reached in the last two weeks)."""
    patient = (await db.execute(accessible_patients(user))).scalar_one_or_none()
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient profile not found.")
    goals = await service.goals_of(db, patient.id, current=True)
    return await service.with_progress(db, patient.id, goals)
