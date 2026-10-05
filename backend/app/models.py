"""Imports every model so Base.metadata is complete (Alembic, tests)."""

from app.audit.models import AuditLog
from app.clinical.models import ConstraintSet
from app.clinicians.models import Clinician, PatientClinician
from app.core.db import Base
from app.exercises.models import Exercise, Stimulus
from app.patients.models import Patient
from app.performance.models import PerformanceProfile
from app.sessions.models import ExerciseResponse, PracticeSession
from app.users.models import User

__all__ = [
    "AuditLog",
    "Base",
    "Clinician",
    "ConstraintSet",
    "Exercise",
    "ExerciseResponse",
    "Patient",
    "PatientClinician",
    "PerformanceProfile",
    "PracticeSession",
    "Stimulus",
    "User",
]
