import os

# Must be set before any app import: tests use an isolated database and Redis DB.
os.environ["APP_ENV"] = "test"
os.environ["POSTGRES_DB"] = "stroke_recovery_test"
os.environ["REDIS_URL"] = "redis://localhost:6379/15"

from collections.abc import AsyncIterator  # noqa: E402
from pathlib import Path  # noqa: E402

import httpx  # noqa: E402
import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from sqlalchemy import select, text  # noqa: E402
from sqlalchemy.ext.asyncio import create_async_engine  # noqa: E402

from app.clinicians.models import Clinician, PatientClinician  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.core.db import SessionLocal  # noqa: E402
from app.core.passwords import hash_password  # noqa: E402
from app.core.redis import redis_client  # noqa: E402
from app.exercises.catalog import sync_stimuli  # noqa: E402
from app.main import app  # noqa: E402
from app.patients.models import Patient  # noqa: E402
from app.users.models import Role, User  # noqa: E402

ORIGIN = "http://localhost:3000"
PASSWORD = "correct horse battery staple"
_PW_HASH = hash_password(PASSWORD)


@pytest.fixture(scope="session", autouse=True)
def migrate() -> None:
    cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    command.upgrade(cfg, "head")


@pytest.fixture(scope="session", autouse=True)
async def stimuli(migrate: None) -> None:
    async with SessionLocal() as db:
        await sync_stimuli(db)


@pytest.fixture(autouse=True)
async def clean_state() -> AsyncIterator[None]:
    # Cleanup runs as the schema owner: the runtime role cannot truncate audit_logs.
    engine = create_async_engine(get_settings().migration_database_url)
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "TRUNCATE exercise_responses, exercises, practice_sessions, performance_profiles,"
                " clinical_constraint_sets, patient_clinicians, patients, clinicians, users,"
                " audit_logs CASCADE"
            )
        )
    await engine.dispose()
    await redis_client.flushdb()
    yield


def make_client(origin: str | None = ORIGIN) -> httpx.AsyncClient:
    headers = {"Origin": origin} if origin else {}
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=app), base_url="http://testserver", headers=headers
    )


@pytest.fixture
def client() -> httpx.AsyncClient:
    return make_client()


async def create_user(email: str, role: Role, *, active: bool = True) -> User:
    async with SessionLocal() as db:
        user = User(
            email=email,
            role=role,
            display_name=email.split("@")[0],
            password_hash=_PW_HASH,
            is_active=active,
        )
        db.add(user)
        await db.flush()
        if role is Role.PATIENT:
            db.add(Patient(user_id=user.id))
        elif role is Role.CLINICIAN:
            db.add(Clinician(user_id=user.id))
        await db.commit()
        return user


async def patient_id(user: User) -> str:
    async with SessionLocal() as db:
        return str(await db.scalar(select(Patient.id).where(Patient.user_id == user.id)))


async def assign(patient_user: User, clinician_user: User) -> None:
    async with SessionLocal() as db:
        pid = await db.scalar(select(Patient.id).where(Patient.user_id == patient_user.id))
        cid = await db.scalar(select(Clinician.id).where(Clinician.user_id == clinician_user.id))
        db.add(PatientClinician(patient_id=pid, clinician_id=cid))
        await db.commit()


async def login(client: httpx.AsyncClient, email: str, password: str = PASSWORD) -> httpx.Response:
    return await client.post("/api/v1/auth/login", json={"email": email, "password": password})
