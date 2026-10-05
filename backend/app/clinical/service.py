import uuid

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical.models import ConstraintSet
from app.exercises.types import MAX_DIFFICULTY, MIN_DIFFICULTY, ExerciseType, ResponseMode


class ConstraintSetIn(BaseModel):
    allowed_exercise_types: list[ExerciseType] = Field(min_length=1)
    allowed_response_modes: list[ResponseMode] = Field(min_length=1)
    allowed_categories: list[str] | None = None
    min_difficulty: int = Field(ge=MIN_DIFFICULTY, le=MAX_DIFFICULTY)
    max_difficulty: int = Field(ge=MIN_DIFFICULTY, le=MAX_DIFFICULTY)
    max_exercises_per_session: int = Field(ge=1, le=50)
    advance_after_correct: int = Field(default=3, ge=1, le=10)
    step_back_after_incorrect: int = Field(default=2, ge=1, le=10)
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _range(self) -> "ConstraintSetIn":
        if self.min_difficulty > self.max_difficulty:
            raise ValueError("min_difficulty must not exceed max_difficulty")
        return self


class ConstraintSetOut(ConstraintSetIn):
    id: str
    version: int

    @classmethod
    def of(cls, cs: ConstraintSet) -> "ConstraintSetOut":
        return cls(
            id=str(cs.id),
            version=cs.version,
            allowed_exercise_types=cs.allowed_exercise_types,
            allowed_response_modes=cs.allowed_response_modes,
            allowed_categories=cs.allowed_categories,
            min_difficulty=cs.min_difficulty,
            max_difficulty=cs.max_difficulty,
            max_exercises_per_session=cs.max_exercises_per_session,
            advance_after_correct=cs.advance_after_correct,
            step_back_after_incorrect=cs.step_back_after_incorrect,
            note=cs.note,
        )


async def latest_constraints(db: AsyncSession, patient_id: uuid.UUID) -> ConstraintSet | None:
    stmt = (
        select(ConstraintSet)
        .where(ConstraintSet.patient_id == patient_id)
        .order_by(ConstraintSet.version.desc())
        .limit(1)
    )
    return (await db.execute(stmt)).scalar_one_or_none()


async def create_version(
    db: AsyncSession, patient_id: uuid.UUID, data: ConstraintSetIn, author_user_id: uuid.UUID
) -> ConstraintSet:
    """Append a new immutable version. Takes effect for the very next exercise issued."""
    current = await db.scalar(
        select(func.max(ConstraintSet.version)).where(ConstraintSet.patient_id == patient_id)
    )
    cs = ConstraintSet(
        patient_id=patient_id,
        version=(current or 0) + 1,
        created_by_user_id=author_user_id,
        **{
            **data.model_dump(),
            "allowed_exercise_types": [t.value for t in data.allowed_exercise_types],
            "allowed_response_modes": [m.value for m in data.allowed_response_modes],
        },
    )
    db.add(cs)
    await db.flush()
    return cs
