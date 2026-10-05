"""Imports every model so Base.metadata is complete (Alembic, tests)."""

from app.audit.models import AuditLog
from app.clinicians.models import Clinician, PatientClinician
from app.core.db import Base
from app.patients.models import Patient
from app.users.models import User

__all__ = ["AuditLog", "Base", "Clinician", "Patient", "PatientClinician", "User"]
