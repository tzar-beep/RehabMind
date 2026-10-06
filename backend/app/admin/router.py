import uuid

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.auth.deps import AdminUser, DbDep
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


def _summary(u: User) -> UserSummary:
    return UserSummary(
        id=str(u.id),
        email=u.email,
        role=u.role,
        display_name=u.display_name,
        is_active=u.is_active,
    )


@router.get("/users", response_model=list[UserSummary])
async def list_users(_: AdminUser, db: DbDep) -> list[UserSummary]:
    rows = await db.execute(select(User).order_by(User.created_at))
    return [_summary(u) for u in rows.scalars()]


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
