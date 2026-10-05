from fastapi import APIRouter
from pydantic import BaseModel
from sqlalchemy import select

from app.auth.deps import AdminUser, DbDep
from app.users.models import Role, User

router = APIRouter(prefix="/admin", tags=["admin"])


class UserSummary(BaseModel):
    """Account administration only; deliberately excludes all clinical data."""

    id: str
    email: str
    role: Role
    display_name: str
    is_active: bool


@router.get("/users", response_model=list[UserSummary])
async def list_users(_: AdminUser, db: DbDep) -> list[UserSummary]:
    rows = await db.execute(select(User).order_by(User.created_at))
    return [
        UserSummary(
            id=str(u.id),
            email=u.email,
            role=u.role,
            display_name=u.display_name,
            is_active=u.is_active,
        )
        for u in rows.scalars()
    ]
