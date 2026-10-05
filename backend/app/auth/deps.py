import uuid
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.sessions import SessionStore
from app.core.config import Settings, get_settings
from app.core.db import get_db
from app.core.redis import get_redis
from app.users.models import Role, User

DbDep = Annotated[AsyncSession, Depends(get_db)]
SettingsDep = Annotated[Settings, Depends(get_settings)]


def get_session_store(
    redis: Annotated[Redis, Depends(get_redis)], settings: SettingsDep
) -> SessionStore:
    return SessionStore(redis, settings)


SessionStoreDep = Annotated[SessionStore, Depends(get_session_store)]


@dataclass(frozen=True)
class CurrentUser:
    id: uuid.UUID
    role: Role
    display_name: str
    session_token: str


_UNAUTHENTICATED = HTTPException(status.HTTP_401_UNAUTHORIZED, "Not signed in.")


async def get_current_user(
    request: Request, db: DbDep, store: SessionStoreDep, settings: SettingsDep
) -> CurrentUser:
    token = request.cookies.get(settings.session_cookie_name)
    if not token:
        raise _UNAUTHENTICATED
    session = await store.get(token)
    if session is None:
        raise _UNAUTHENTICATED
    user = await db.get(User, uuid.UUID(session.user_id))
    if user is None or not user.is_active or user.role.value != session.role:
        await store.revoke(token)
        raise _UNAUTHENTICATED
    return CurrentUser(user.id, user.role, user.display_name, token)


CurrentUserDep = Annotated[CurrentUser, Depends(get_current_user)]


def require_roles(*roles: Role) -> Callable[..., Awaitable[CurrentUser]]:
    async def dependency(user: CurrentUserDep) -> CurrentUser:
        if user.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "Not permitted.")
        return user

    return dependency


PatientUser = Annotated[CurrentUser, Depends(require_roles(Role.PATIENT))]
ClinicianUser = Annotated[CurrentUser, Depends(require_roles(Role.CLINICIAN))]
AdminUser = Annotated[CurrentUser, Depends(require_roles(Role.ADMIN))]
