"""Therapy goals: what they say to the patient, and how far along they are.

Progress is measured, never entered: name_words counts words the patient named on their
own the last three times (the clinician's Words view, "secure"); practice_days counts days
with at least one answer since Monday (UTC) this week.
"""

import uuid
from datetime import UTC, date, datetime, timedelta
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.clinicians.insights import word_progress
from app.goals.models import TherapyGoal
from app.sessions.models import ExerciseResponse

MAX_ACTIVE = 3
# Category words a patient reads: "Name 10 home words on your own".
CATEGORY_WORDS = {
    "household": "home",
    "personal": "everyday",
    "food": "food",
    "transport": "travel",
    "animals": "animal",
    "tools": "tool",
    "music": "music",
    "nature": "outdoor",
}


class GoalIn(BaseModel):
    kind: Literal["name_words", "practice_days"]
    target: int = Field(ge=1, le=200)
    category: str | None = None
    due_on: date | None = None

    @model_validator(mode="after")
    def _valid(self) -> "GoalIn":
        if self.kind == "practice_days":
            if self.target > 7:
                raise ValueError("a week has 7 days")
            self.category = None
        elif self.category is not None and self.category not in CATEGORY_WORDS:
            raise ValueError("unknown picture category")
        return self


class GoalOut(BaseModel):
    id: str
    kind: str
    target: int
    category: str | None
    due_on: date | None
    status: str
    title: str  # plain words for the patient
    progress: int
    created_at: datetime
    achieved_at: datetime | None


def title(goal: TherapyGoal) -> str:
    if goal.kind == "practice_days":
        return f"Practise on {goal.target} {'day' if goal.target == 1 else 'days'} this week"
    group = f"{CATEGORY_WORDS[goal.category]} " if goal.category else ""
    return f"Name {goal.target} {group}{'word' if goal.target == 1 else 'words'} on your own"


async def _days_this_week(db: AsyncSession, patient_id: uuid.UUID) -> int:
    now = datetime.now(UTC)
    monday = datetime(now.year, now.month, now.day, tzinfo=UTC) - timedelta(days=now.weekday())
    return (
        await db.scalar(
            select(func.count(func.distinct(func.date(ExerciseResponse.created_at)))).where(
                ExerciseResponse.patient_id == patient_id, ExerciseResponse.created_at >= monday
            )
        )
        or 0
    )


async def with_progress(
    db: AsyncSession, patient_id: uuid.UUID, goals: list[TherapyGoal]
) -> list[GoalOut]:
    """Goals with their current progress. A word goal reached for the first time is marked
    achieved (and stays achieved: it is a milestone, even if a word later slips)."""
    words = (
        await word_progress(db, patient_id) if any(g.kind == "name_words" for g in goals) else []
    )
    days = (
        await _days_this_week(db, patient_id)
        if any(g.kind == "practice_days" for g in goals)
        else 0
    )
    out = []
    for g in goals:
        if g.kind == "practice_days":
            progress = days
        else:
            progress = sum(
                w.status == "secure" and (g.category is None or w.category == g.category)
                for w in words
            )
            if g.status == "active" and progress >= g.target:
                g.status, g.achieved_at = "achieved", datetime.now(UTC)
        out.append(
            GoalOut(
                id=str(g.id),
                kind=g.kind,
                target=g.target,
                category=g.category,
                due_on=g.due_on,
                status=g.status,
                title=title(g),
                progress=min(progress, g.target),
                created_at=g.created_at,
                achieved_at=g.achieved_at,
            )
        )
    await db.commit()
    return out


async def goals_of(db: AsyncSession, patient_id: uuid.UUID, *, current: bool) -> list[TherapyGoal]:
    """current: active goals and those achieved in the last two weeks (for the patient)."""
    stmt = select(TherapyGoal).where(TherapyGoal.patient_id == patient_id)
    if current:
        recent = datetime.now(UTC) - timedelta(days=14)
        stmt = stmt.where(
            (TherapyGoal.status == "active")
            | ((TherapyGoal.status == "achieved") & (TherapyGoal.achieved_at >= recent))
        )
    return list((await db.execute(stmt.order_by(TherapyGoal.created_at.desc()))).scalars())
