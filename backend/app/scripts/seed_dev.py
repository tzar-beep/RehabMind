"""Create development accounts. Refuses to run outside local development.

Usage:  uv run python -m app.scripts.seed_dev
Password for all seed accounts: SEED_DEV_PASSWORD in the root .env.
"""

import asyncio
import sys

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical.service import ConstraintSetIn, create_version, latest_constraints
from app.clinicians.models import Clinician, PatientClinician
from app.core.config import Settings, get_settings
from app.core.db import SessionLocal
from app.core.passwords import hash_password
from app.exercises.catalog import sync_stimuli
from app.exercises.types import ExerciseType, ResponseMode
from app.patients.models import Patient
from app.users.models import Role, User

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}
ACCOUNTS = [
    ("patient@recovery.local", Role.PATIENT, "Alex"),
    ("clinician@recovery.local", Role.CLINICIAN, "Dr. Morgan Lee"),
    ("admin@recovery.local", Role.ADMIN, "Site Admin"),
]

DEV_CONSTRAINTS = ConstraintSetIn(
    allowed_exercise_types=[ExerciseType.PICTURE_NAMING],
    allowed_response_modes=[ResponseMode.TEXT, ResponseMode.SPEECH],
    min_difficulty=1,
    max_difficulty=3,
    max_exercises_per_session=8,
    note="Development default",
)


def assert_seed_allowed(settings: Settings) -> None:
    if settings.app_env != "development":
        raise RuntimeError("dev seed refused: APP_ENV is not 'development'")
    if settings.postgres_host not in LOCAL_HOSTS:
        raise RuntimeError("dev seed refused: database host is not local")


async def _upsert_user(db: AsyncSession, email: str, role: Role, name: str, pw: str) -> User:
    user = (await db.execute(select(User).where(User.email == email))).scalar_one_or_none()
    if user is None:
        user = User(email=email, role=role, display_name=name, password_hash=hash_password(pw))
        db.add(user)
        await db.flush()
    return user


async def seed(password: str) -> None:
    async with SessionLocal() as db:
        users = {r: await _upsert_user(db, e, r, n, password) for e, r, n in ACCOUNTS}
        patient = (
            await db.execute(select(Patient).where(Patient.user_id == users[Role.PATIENT].id))
        ).scalar_one_or_none() or Patient(user_id=users[Role.PATIENT].id)
        clinician = (
            await db.execute(select(Clinician).where(Clinician.user_id == users[Role.CLINICIAN].id))
        ).scalar_one_or_none() or Clinician(user_id=users[Role.CLINICIAN].id)
        db.add_all([patient, clinician])
        await db.flush()
        if await db.get(PatientClinician, (patient.id, clinician.id)) is None:
            db.add(PatientClinician(patient_id=patient.id, clinician_id=clinician.id))
        current = await latest_constraints(db, patient.id)
        if current is None or set(current.allowed_response_modes) != {
            m.value for m in DEV_CONSTRAINTS.allowed_response_modes
        }:
            await create_version(db, patient.id, DEV_CONSTRAINTS, users[Role.CLINICIAN].id)
        await db.commit()
        await sync_stimuli(db)


def main() -> None:
    settings = get_settings()
    try:
        assert_seed_allowed(settings)
    except RuntimeError as e:
        sys.exit(str(e))
    secret = settings.seed_dev_password
    password = secret.get_secret_value() if secret else ""
    if len(password) < 12:
        sys.exit("SEED_DEV_PASSWORD must be set (>= 12 chars) in .env")
    asyncio.run(seed(password))
    print("seeded:", ", ".join(e for e, _, _ in ACCOUNTS))


if __name__ == "__main__":
    main()
