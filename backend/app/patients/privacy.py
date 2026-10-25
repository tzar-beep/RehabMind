"""The patient's own view of their data: who can see their practice, stopping sharing with
family, and a copy of everything kept about them (data portability)."""

import json
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import aliased

from app.audit import service as audit
from app.auth.deps import DbDep, PatientUser
from app.carers.models import Encouragement, PatientCarer
from app.clinicians.models import Clinician, PatientClinician
from app.exercises.models import Exercise, Stimulus
from app.goals.models import TherapyGoal
from app.patients.access import accessible_patients
from app.patients.models import Patient
from app.phrases.models import ScriptPractice
from app.sessions.models import ExerciseResponse, PracticeSession
from app.users.models import User
from app.wellbeing.models import MoodCheckin

router = APIRouter(prefix="/practice/my-information", tags=["privacy"])


class FamilyMember(BaseModel):
    user_id: str
    name: str
    relationship: str


class WhoCanSee(BaseModel):
    care_team: list[str]
    family: list[FamilyMember]


async def _patient(user: PatientUser, db: DbDep) -> Patient:
    patient = (await db.execute(accessible_patients(user))).scalar_one_or_none()
    if patient is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient profile not found.")
    return patient


@router.get("", response_model=WhoCanSee)
async def who_can_see(user: PatientUser, db: DbDep) -> WhoCanSee:
    patient = await _patient(user, db)
    clinician_user = aliased(User)
    team = await db.scalars(
        select(clinician_user.display_name)
        .join(Clinician, Clinician.user_id == clinician_user.id)
        .join(PatientClinician, PatientClinician.clinician_id == Clinician.id)
        .where(PatientClinician.patient_id == patient.id)
        .order_by(clinician_user.display_name)
    )
    family = await db.execute(
        select(User.id, User.display_name, PatientCarer.relationship)
        .join(PatientCarer, PatientCarer.user_id == User.id)
        .where(PatientCarer.patient_id == patient.id)
        .order_by(User.display_name)
    )
    return WhoCanSee(
        care_team=list(team),
        family=[FamilyMember(user_id=str(i), name=n, relationship=r) for i, n, r in family],
    )


@router.delete("/family/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def stop_sharing(user_id: uuid.UUID, user: PatientUser, db: DbDep) -> None:
    """The patient stops sharing with a family member. Only an admin can link them again."""
    patient = await _patient(user, db)
    link = await db.get(PatientCarer, (patient.id, user_id))
    if link is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found.")
    await db.delete(link)
    await audit.record(
        db,
        "carer.unlinked_by_patient",
        "success",
        actor_user_id=user.id,
        target_type="patient",
        target_id=patient.id,
        details={"carer_user_id": str(user_id)},
        commit=False,
    )
    await db.commit()


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


@router.get("/export")
async def export(user: PatientUser, db: DbDep) -> Response:
    """Everything kept about the patient's practice, as a JSON file. No recordings exist to
    include: audio is deleted after transcription."""
    patient = await _patient(user, db)
    answers = await db.execute(
        select(ExerciseResponse, Exercise)
        .join(Exercise, Exercise.id == ExerciseResponse.exercise_id)
        .where(ExerciseResponse.patient_id == patient.id)
        .order_by(ExerciseResponse.created_at)
    )
    sessions = await db.scalars(
        select(PracticeSession)
        .where(PracticeSession.patient_id == patient.id)
        .order_by(PracticeSession.started_at)
    )
    data = {
        "exported_at": datetime.now(UTC).isoformat(),
        "name": user.display_name,
        "about": "Your practice in RehabMind. Voice recordings are never kept.",
        "sessions": [
            {
                "started": _iso(s.started_at),
                "finished": _iso(s.completed_at),
                "status": s.status,
                "how_it_felt": s.difficulty_rating,
            }
            for s in sessions
        ],
        "answers": [
            {
                "when": _iso(r.created_at),
                "exercise": ex.exercise_type,
                "picture": ex.expected.get("target"),
                "your_answer": r.text,
                "how_you_answered": r.mode,
                "result": r.outcome,
            }
            for r, ex in answers.all()
        ],
        "goals": [
            {"kind": g.kind, "target": g.target, "category": g.category, "status": g.status}
            for g in await db.scalars(
                select(TherapyGoal).where(TherapyGoal.patient_id == patient.id)
            )
        ],
        "own_words": [
            s.target
            for s in await db.scalars(
                select(Stimulus).where(Stimulus.owner_patient_id == patient.id, Stimulus.is_active)
            )
        ],
        "moods": [
            {"day": m.day.isoformat(), "mood": m.mood}
            for m in await db.scalars(
                select(MoodCheckin).where(MoodCheckin.patient_id == patient.id)
            )
        ],
        "phrases_practised": [
            {"script": p.script_id, "when": _iso(p.created_at), "lines_said": p.lines_said}
            for p in await db.scalars(
                select(ScriptPractice).where(ScriptPractice.patient_id == patient.id)
            )
        ],
        "notes_from_family": [
            {"when": _iso(m.created_at), "text": m.text}
            for m in await db.scalars(
                select(Encouragement).where(Encouragement.patient_id == patient.id)
            )
        ],
    }
    await audit.record(
        db,
        "patient.data_exported",
        "success",
        actor_user_id=user.id,
        target_type="patient",
        target_id=patient.id,
    )
    return Response(
        json.dumps(data, indent=2, ensure_ascii=False),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="my-rehabmind-information.json"'},
    )
