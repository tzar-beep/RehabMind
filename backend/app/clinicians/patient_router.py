"""Clinician read views of one assigned patient. Every route resolves the patient through
`get_accessible_patient` first: unassigned or unknown patients are indistinguishable (404)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.audit import service as audit
from app.auth.deps import ClinicianUser, DbDep
from app.clinicians import insights
from app.clinicians.schemas import (
    PatientOverview,
    SessionDetail,
    SessionPage,
    TrendPoint,
)
from app.patients.access import get_accessible_patient
from app.patients.models import Patient

router = APIRouter(prefix="/patients/{patient_id}", tags=["clinician-insights"])


async def assigned_patient(patient_id: uuid.UUID, user: ClinicianUser, db: DbDep) -> Patient:
    patient = await get_accessible_patient(db, user, patient_id)
    if patient is None:
        await audit.record(
            db,
            "patient.read",
            "denied",
            actor_user_id=user.id,
            target_type="patient",
            target_id=patient_id,
        )
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Patient not found.")
    return patient


AssignedPatient = Annotated[Patient, Depends(assigned_patient)]


@router.get("/overview", response_model=PatientOverview)
async def patient_overview(patient: AssignedPatient, db: DbDep) -> PatientOverview:
    return await insights.overview(db, patient)


@router.get("/trends", response_model=list[TrendPoint])
async def patient_trends(patient: AssignedPatient, db: DbDep) -> list[TrendPoint]:
    return await insights.trends(db, patient.id)


@router.get("/sessions", response_model=SessionPage)
async def patient_sessions(
    patient: AssignedPatient,
    db: DbDep,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> SessionPage:
    items, total = await insights.sessions_page(db, patient.id, limit, offset)
    return SessionPage(items=items, total=total, limit=limit, offset=offset)


@router.get("/sessions/{session_id}", response_model=SessionDetail)
async def patient_session(
    session_id: uuid.UUID, patient: AssignedPatient, db: DbDep
) -> SessionDetail:
    detail = await insights.session_detail(db, patient.id, session_id)
    if detail is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Session not found.")
    return detail
