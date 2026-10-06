"""Account creation shared by the admin API and the `create_user` CLI."""

import secrets
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.audit import service as audit
from app.clinicians.models import Clinician, PatientClinician
from app.core.passwords import hash_password
from app.patients.models import Patient
from app.users.models import Role, User

# No look-alike characters (0/O, 1/l/I), so a printed password is easy to pass on.
_ALPHABET = "abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789"


class AccountError(ValueError):
    """The request cannot be fulfilled (duplicate email, unknown clinician, ...)."""


def generate_password() -> str:
    """16 random characters (~92 bits) in four groups, e.g. `k7Pq-x2Vn-Rt8m-Hw4z`."""
    chars = "".join(secrets.choice(_ALPHABET) for _ in range(16))
    return "-".join(chars[i : i + 4] for i in range(0, 16, 4))


async def clinician_for_user(db: AsyncSession, user_id: uuid.UUID) -> Clinician | None:
    return await db.scalar(select(Clinician).where(Clinician.user_id == user_id))


async def create_account(
    db: AsyncSession,
    *,
    email: str,
    name: str,
    role: Role,
    password: str,
    clinician: Clinician | None = None,
    actor_user_id: uuid.UUID | None = None,
    via: str,
) -> User:
    email = User.normalize_email(email)
    if await db.scalar(select(User).where(User.email == email)):
        raise AccountError("An account with this email already exists.")
    if clinician is not None and role is not Role.PATIENT:
        raise AccountError("Only patients are assigned to a clinician.")
    user = User(email=email, display_name=name, role=role, password_hash=hash_password(password))
    db.add(user)
    await db.flush()
    if role is Role.PATIENT:
        patient = Patient(user_id=user.id)
        db.add(patient)
        await db.flush()
        if clinician is not None:
            db.add(PatientClinician(patient_id=patient.id, clinician_id=clinician.id))
    elif role is Role.CLINICIAN:
        db.add(Clinician(user_id=user.id))
    await audit.record(
        db,
        "user.created",
        "success",
        actor_user_id=actor_user_id,
        target_type="user",
        target_id=user.id,
        details={"role": role.value, "via": via},
        commit=False,
    )
    await db.commit()
    return user
