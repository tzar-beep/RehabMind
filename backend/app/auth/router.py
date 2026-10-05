from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import BaseModel, Field
from redis.asyncio import Redis
from sqlalchemy import select

from app.audit import service as audit
from app.auth.deps import CurrentUserDep, DbDep, SessionStoreDep, SettingsDep
from app.auth.rate_limit import LoginRateLimiter
from app.core.config import Settings
from app.core.passwords import hash_password, needs_rehash, verify_password
from app.core.redis import get_redis
from app.users.models import Role, User

router = APIRouter(prefix="/auth", tags=["auth"])


class LoginIn(BaseModel):
    # Not EmailStr: login only looks the address up; format rules belong to registration.
    email: str = Field(min_length=3, max_length=320)
    password: str = Field(min_length=1, max_length=256)


class MeOut(BaseModel):
    id: str
    role: Role
    display_name: str


def client_ip(request: Request, settings: Settings) -> str:
    if settings.trust_proxy_headers and (fwd := request.headers.get("x-forwarded-for")):
        return fwd.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _set_cookie(response: Response, settings: Settings, token: str) -> None:
    response.set_cookie(
        settings.session_cookie_name,
        token,
        max_age=settings.session_absolute_timeout_seconds,
        httponly=True,
        secure=settings.is_production,
        samesite="lax",
        path="/",
    )


@router.post("/login", response_model=MeOut)
async def login(
    body: LoginIn,
    request: Request,
    response: Response,
    db: DbDep,
    store: SessionStoreDep,
    settings: SettingsDep,
    redis: Annotated[Redis, Depends(get_redis)],
) -> MeOut:
    email = User.normalize_email(body.email)
    limiter = LoginRateLimiter(
        redis,
        max_failures=settings.login_max_failures_per_account,
        max_ip=settings.login_max_attempts_per_ip,
        window=settings.login_rate_window_seconds,
    )
    if not await limiter.allow_attempt(email, client_ip(request, settings)):
        await audit.record(db, "auth.login", "denied", details={"reason": "rate_limited"})
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, "Too many attempts. Please wait and try again."
        )

    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if not verify_password(user.password_hash if user else None, body.password) or not (
        user and user.is_active
    ):
        await limiter.record_failure(email)
        await audit.record(
            db,
            "auth.login",
            "failure",
            actor_user_id=user.id if user else None,
            details={"reason": "invalid_credentials"},
        )
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email or password is incorrect.")

    await limiter.reset(email)
    # Prevent session fixation: discard any session presented with this request.
    if old := request.cookies.get(settings.session_cookie_name):
        await store.revoke(old)
    token = await store.create(user.id, user.role.value)
    _set_cookie(response, settings, token)

    if needs_rehash(user.password_hash):
        user.password_hash = hash_password(body.password)
    user.last_login_at = datetime.now(UTC)
    await audit.record(db, "auth.login", "success", actor_user_id=user.id, commit=False)
    await db.commit()
    return MeOut(id=str(user.id), role=user.role, display_name=user.display_name)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    user: CurrentUserDep,
    response: Response,
    db: DbDep,
    store: SessionStoreDep,
    settings: SettingsDep,
) -> None:
    await store.revoke(user.session_token)
    response.delete_cookie(settings.session_cookie_name, path="/")
    await audit.record(db, "auth.logout", "success", actor_user_id=user.id)


@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(
    user: CurrentUserDep,
    response: Response,
    db: DbDep,
    store: SessionStoreDep,
    settings: SettingsDep,
) -> None:
    await store.revoke_all(user.id)
    response.delete_cookie(settings.session_cookie_name, path="/")
    await audit.record(db, "auth.logout_all", "success", actor_user_id=user.id)


@router.get("/me", response_model=MeOut)
async def me(user: CurrentUserDep) -> MeOut:
    return MeOut(id=str(user.id), role=user.role, display_name=user.display_name)
