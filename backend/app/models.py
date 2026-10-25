"""Imports every model so Base.metadata is complete (Alembic, tests)."""

from app.ai.models import AIGeneration
from app.audit.models import AuditLog
from app.carers.models import Encouragement, PatientCarer
from app.clinical.models import ConstraintSet
from app.clinicians.models import Clinician, PatientClinician
from app.core.db import Base
from app.exercises.models import Exercise, Stimulus
from app.goals.models import TherapyGoal
from app.patients.models import Patient
from app.performance.models import PerformanceProfile
from app.personal.models import PersonalPhoto
from app.phrases.models import ScriptPractice
from app.sessions.models import ExerciseResponse, PracticeSession
from app.speech.models import AudioAsset
from app.users.models import User
from app.wellbeing.models import MoodCheckin

__all__ = [
    "AIGeneration",
    "AudioAsset",
    "AuditLog",
    "Base",
    "Clinician",
    "ConstraintSet",
    "Encouragement",
    "Exercise",
    "ExerciseResponse",
    "Patient",
    "MoodCheckin",
    "PatientCarer",
    "PatientClinician",
    "PerformanceProfile",
    "PersonalPhoto",
    "PracticeSession",
    "ScriptPractice",
    "Stimulus",
    "TherapyGoal",
    "User",
]
