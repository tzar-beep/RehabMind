import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.audit import service as audit
from app.auth.deps import AdminUser, DbDep, SessionStoreDep
from app.clinicians.models import Clinician, PatientClinician
from app.core.passwords import hash_password
from app.patients.models import Patient
from app.users.models import Role, User
from app.users.provisioning import (
    AccountError,
    clinician_for_user,
    create_account,
    generate_password,
)

router = APIRouter(prefix="/admin", tags=["admin"])


class UserSummary(BaseModel):
    """Account administration only; deliberately excludes all clinical data."""

    id: str
    email: str
    role: Role
    display_name: str
    is_active: bool
    # Patients only: names of the assigned clinicians (an administrative fact, not
    # clinical data). Empty means nobody can see or plan this patient's practice yet.
    care_team: list[str] = []


class NewUser(BaseModel):
    email: str = Field(min_length=3, max_length=254, pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    display_name: str = Field(min_length=1, max_length=120)
    role: Role
    # Patients only: the user id of the clinician who will care for them.
    clinician_user_id: uuid.UUID | None = None


class CreatedUser(BaseModel):
    user: UserSummary
    # Shown to the admin exactly once; only its Argon2id hash is stored.
    initial_password: str


def _summary(u: User, care_team: list[str] | None = None) -> UserSummary:
    return UserSummary(
        id=str(u.id),
        email=u.email,
        role=u.role,
        display_name=u.display_name,
        is_active=u.is_active,
        care_team=care_team or [],
    )


async def _care_teams(db: DbDep) -> dict[uuid.UUID, list[str]]:
    clinician_user = aliased(User)
    rows = await db.execute(
        select(Patient.user_id, clinician_user.display_name)
        .join(PatientClinician, PatientClinician.patient_id == Patient.id)
        .join(Clinician, Clinician.id == PatientClinician.clinician_id)
        .join(clinician_user, clinician_user.id == Clinician.user_id)
        .order_by(clinician_user.display_name)
    )
    teams: dict[uuid.UUID, list[str]] = {}
    for patient_user_id, name in rows.all():
        teams.setdefault(patient_user_id, []).append(name)
    return teams


@router.get("/users", response_model=list[UserSummary])
async def list_users(_: AdminUser, db: DbDep) -> list[UserSummary]:
    rows = await db.execute(select(User).order_by(User.created_at))
    teams = await _care_teams(db)
    return [_summary(u, teams.get(u.id)) for u in rows.scalars()]


async def _user(db: DbDep, user_id: uuid.UUID) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found.")
    return user


class NewPassword(BaseModel):
    # Shown to the admin exactly once; only its Argon2id hash is stored.
    initial_password: str


@router.post("/users/{user_id}/password", response_model=NewPassword)
async def reset_password(
    user_id: uuid.UUID, admin: AdminUser, db: DbDep, store: SessionStoreDep
) -> NewPassword:
    """For someone who lost their first password: a new generated one, shown once.
    Every existing session of that user is signed out."""
    user = await _user(db, user_id)
    password = generate_password()
    user.password_hash = hash_password(password)
    await audit.record(
        db,
        "user.password_reset",
        "success",
        actor_user_id=admin.id,
        target_type="user",
        target_id=user.id,
        commit=False,
    )
    await db.commit()
    await store.revoke_all(user.id)
    return NewPassword(initial_password=password)


class ActiveIn(BaseModel):
    active: bool


@router.put("/users/{user_id}/active", response_model=UserSummary)
async def set_active(
    user_id: uuid.UUID, body: ActiveIn, admin: AdminUser, db: DbDep, store: SessionStoreDep
) -> UserSummary:
    """Disable (sign-in refused, all sessions ended) or re-enable an account."""
    if user_id == admin.id:
        raise HTTPException(status.HTTP_409_CONFLICT, "You cannot disable your own account.")
    user = await _user(db, user_id)
    user.is_active = body.active
    await audit.record(
        db,
        "user.enabled" if body.active else "user.disabled",
        "success",
        actor_user_id=admin.id,
        target_type="user",
        target_id=user.id,
        commit=False,
    )
    await db.commit()
    if not body.active:
        await store.revoke_all(user.id)
    return _summary(user, (await _care_teams(db)).get(user.id))


class AssignIn(BaseModel):
    clinician_user_id: uuid.UUID


@router.post("/users/{user_id}/care-team", response_model=UserSummary)
async def assign_clinician(
    user_id: uuid.UUID, body: AssignIn, admin: AdminUser, db: DbDep
) -> UserSummary:
    """Add a clinician to a patient's care team (idempotent)."""
    user = await _user(db, user_id)
    patient = await db.scalar(select(Patient).where(Patient.user_id == user.id))
    if patient is None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Only patients have a care team.")
    clinician = await clinician_for_user(db, body.clinician_user_id)
    if clinician is None:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Clinician not found.")
    if await db.get(PatientClinician, (patient.id, clinician.id)) is None:
        db.add(PatientClinician(patient_id=patient.id, clinician_id=clinician.id))
        await audit.record(
            db,
            "patient.assigned",
            "success",
            actor_user_id=admin.id,
            target_type="patient",
            target_id=patient.id,
            details={"clinician_id": str(clinician.id)},
            commit=False,
        )
        await db.commit()
    return _summary(user, (await _care_teams(db)).get(user.id))


@router.post("/users", response_model=CreatedUser, status_code=status.HTTP_201_CREATED)
async def create_user(body: NewUser, admin: AdminUser, db: DbDep) -> CreatedUser:
    clinician = None
    if body.clinician_user_id is not None:
        clinician = await clinician_for_user(db, body.clinician_user_id)
        if clinician is None:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Clinician not found.")
    password = generate_password()
    try:
        user = await create_account(
            db,
            email=body.email,
            name=body.display_name.strip(),
            role=body.role,
            password=password,
            clinician=clinician,
            actor_user_id=admin.id,
            via="admin",
        )
    except AccountError as e:
        raise HTTPException(status.HTTP_409_CONFLICT, str(e)) from None
    return CreatedUser(user=_summary(user), initial_password=password)
