"""What a carer sees and does. Activity and goals only: never scores, answers, transcripts
or anything the clinician records."""

import uuid
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.audit import service as audit
from app.auth.deps import CarerUser, DbDep, PatientUser
from app.carers.access import get_supported_patient
from app.carers.models import Encouragement, PatientCarer
from app.goals import service as goals
from app.goals.service import GoalOut
from app.patients.access import accessible_patients
from app.patients.models import Patient
from app.sessions.router import PracticeActivity, activity_of
from app.users.models import User

router = APIRouter(prefix="/carer", tags=["carer"])
patient_router = APIRouter(prefix="/practice", tags=["carer"])

MESSAGES_PER_DAY = 5  # per carer: encouragement, not a chat
SHOWN_FOR = timedelta(days=14)

_NOT_FOUND = HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")


class SupportedPatient(BaseModel):
    id: str
    display_name: str
    relationship: str


class CarerSummary(BaseModel):
    patient: SupportedPatient
    activity: PracticeActivity
    goals: list[GoalOut]


@router.get("/patients", response_model=list[SupportedPatient])
async def my_patients(user: CarerUser, db: DbDep) -> list[SupportedPatient]:
    rows = await db.execute(
        select(Patient.id, User.display_name, PatientCarer.relationship)
        .join(PatientCarer, PatientCarer.patient_id == Patient.id)
        .join(User, User.id == Patient.user_id)
        .where(PatientCarer.user_id == user.id)
        .order_by(User.display_name)
    )
    return [SupportedPatient(id=str(i), display_name=n, relationship=r) for i, n, r in rows]


@router.get("/patients/{patient_id}", response_model=CarerSummary)
async def patient_summary(patient_id: uuid.UUID, user: CarerUser, db: DbDep) -> CarerSummary:
    patient = await get_supported_patient(db, user, patient_id)
    if patient is None:
        raise _NOT_FOUND
    name = await db.scalar(select(User.display_name).where(User.id == patient.user_id))
    relationship = await db.scalar(
        select(PatientCarer.relationship).where(
            PatientCarer.patient_id == patient.id, PatientCarer.user_id == user.id
        )
    )
    current = await goals.goals_of(db, patient.id, current=True)
    return CarerSummary(
        patient=SupportedPatient(
            id=str(patient.id), display_name=name or "", relationship=relationship or ""
        ),
        activity=await activity_of(db, patient.id),
        goals=await goals.with_progress(db, patient.id, current),
    )


class MessageIn(BaseModel):
    text: str = Field(min_length=1, max_length=200)


class Message(BaseModel):
    id: str
    text: str
    author: str
    relationship: str
    created_at: datetime
    seen: bool


def _message(m: Encouragement, author: str, relationship: str) -> Message:
    return Message(
        id=str(m.id),
        text=m.text,
        author=author,
        relationship=relationship,
        created_at=m.created_at,
        seen=m.seen_at is not None,
    )


_LINK = (PatientCarer.patient_id == Encouragement.patient_id) & (
    PatientCarer.user_id == Encouragement.author_id
)


@router.get("/patients/{patient_id}/messages", response_model=list[Message])
async def sent_messages(patient_id: uuid.UUID, user: CarerUser, db: DbDep) -> list[Message]:
    """Notes this carer sent, newest first, and whether the patient has seen them."""
    if await get_supported_patient(db, user, patient_id) is None:
        raise _NOT_FOUND
    rows = await db.execute(
        select(Encouragement, PatientCarer.relationship)
        .join(PatientCarer, _LINK)
        .where(Encouragement.patient_id == patient_id, Encouragement.author_id == user.id)
        .order_by(Encouragement.created_at.desc())
        .limit(10)
    )
    return [_message(m, user.display_name, rel) for m, rel in rows.all()]


@router.post(
    "/patients/{patient_id}/messages", response_model=Message, status_code=status.HTTP_201_CREATED
)
async def send_message(
    patient_id: uuid.UUID, body: MessageIn, user: CarerUser, db: DbDep
) -> Message:
    if await get_supported_patient(db, user, patient_id) is None:
        raise _NOT_FOUND
    text = " ".join(body.text.split())
    if not text:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, "Write a few words first.")
    today = await db.scalar(
        select(func.count()).where(
            Encouragement.author_id == user.id,
            Encouragement.created_at >= datetime.now(UTC) - timedelta(days=1),
        )
    )
    if (today or 0) >= MESSAGES_PER_DAY:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            f"Up to {MESSAGES_PER_DAY} notes a day, so each one stands out.",
        )
    message = Encouragement(patient_id=patient_id, author_id=user.id, text=text)
    db.add(message)
    await audit.record(
        db,
        "encouragement.sent",
        "success",
        actor_user_id=user.id,
        target_type="patient",
        target_id=patient_id,
        commit=False,
    )
    await db.commit()
    await db.refresh(message)
    relationship = await db.scalar(
        select(PatientCarer.relationship).where(
            PatientCarer.patient_id == patient_id, PatientCarer.user_id == user.id
        )
    )
    return _message(message, user.display_name, relationship or "")


@patient_router.get("/messages", response_model=list[Message])
async def my_messages(user: PatientUser, db: DbDep) -> list[Message]:
    """Recent notes from the patient's family, newest first. Reading them marks them seen."""
    patient = (await db.execute(accessible_patients(user))).scalar_one_or_none()
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient profile not found.")
    rows = (
        await db.execute(
            select(Encouragement, User.display_name, PatientCarer.relationship)
            .join(User, User.id == Encouragement.author_id)
            .join(PatientCarer, _LINK)
            .where(
                Encouragement.patient_id == patient.id,
                Encouragement.created_at >= datetime.now(UTC) - SHOWN_FOR,
            )
            .order_by(Encouragement.created_at.desc())
            .limit(3)
        )
    ).all()
    out = [_message(m, name, rel) for m, name, rel in rows]
    now = datetime.now(UTC)
    for m, _, _ in rows:
        m.seen_at = m.seen_at or now
    await db.commit()
    return out
