"""Learned performance model (the ML part): online logistic ability estimation.

For each rehabilitation objective, the model learns one parameter, the patient's ability
theta, from every scored answer since the latest fresh start. It is a one-parameter logistic
(Rasch / Elo-style) model fitted online by stochastic gradient descent on the log-loss:

    p(success | difficulty d) = sigmoid(theta - SCALE * (d - CENTRE))
    theta <- theta + LEARNING_RATE * (y - p)      y = 1 correct, 0.5 close, 0 otherwise

This is the same family of models used for adaptive testing and knowledge tracing. It is
deterministic, explainable and cheap (a few hundred responses at most).

The estimate is *context*, not authority: it tells the LLM (and the clinician) how practice
is going. The difficulty itself is decided by the deterministic progression rule and is
always clamped to the clinician's limits.
"""

import math
import uuid
from dataclasses import asdict, dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.exercises.models import Exercise
from app.exercises.types import OBJECTIVES, Objective
from app.sessions import resets
from app.sessions.models import ExerciseResponse

LEARNING_RATE = 0.4
SCALE = 0.8  # how much harder each difficulty level is, in ability units
CENTRE = 3  # difficulty level at which theta = 0 means a 50% chance of success
HISTORY_LIMIT = 300
RECENT = 10
TREND_WINDOW = 5
OUTCOME_VALUE = {"correct": 1.0, "near_miss": 0.5, "incorrect": 0.0, "skipped": 0.0}


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def p_success(theta: float, difficulty: int) -> float:
    return sigmoid(theta - SCALE * (difficulty - CENTRE))


@dataclass(frozen=True)
class ObjectiveEstimate:
    objective: str
    attempts: int
    ability: float  # theta
    recent_accuracy: float | None  # share correct in the last RECENT answers
    trend: str  # not_enough_data | improving | steady | declining
    status: str  # not_started | needs_practice | progressing | strong

    def predicted_success(self, difficulty: int) -> float:
        return round(p_success(self.ability, difficulty), 2)

    def as_dict(self) -> dict:
        return asdict(self)


def fit(history: list[tuple[str, int]]) -> float:
    """Online SGD over (outcome, difficulty) pairs, oldest first. Returns theta."""
    theta = 0.0
    for outcome, difficulty in history:
        y = OUTCOME_VALUE.get(outcome, 0.0)
        theta += LEARNING_RATE * (y - p_success(theta, difficulty))
    return theta


def _trend(values: list[float]) -> str:
    if len(values) < 2 * TREND_WINDOW:
        return "not_enough_data"
    last = sum(values[-TREND_WINDOW:]) / TREND_WINDOW
    before = sum(values[-2 * TREND_WINDOW : -TREND_WINDOW]) / TREND_WINDOW
    if last - before >= 0.2:
        return "improving"
    if before - last >= 0.2:
        return "declining"
    return "steady"


def estimate(objective: str, history: list[tuple[str, int]]) -> ObjectiveEstimate:
    if not history:
        return ObjectiveEstimate(objective, 0, 0.0, None, "not_enough_data", "not_started")
    recent = [o for o, _ in history[-RECENT:]]
    accuracy = round(sum(o == "correct" for o in recent) / len(recent), 2)
    trend = _trend([OUTCOME_VALUE.get(o, 0.0) for o, _ in history])
    status = (
        "needs_practice"
        if accuracy < 0.5 or trend == "declining"
        else "strong"
        if accuracy >= 0.8
        else "progressing"
    )
    return ObjectiveEstimate(
        objective, len(history), round(fit(history), 3), accuracy, trend, status
    )


async def estimates(db: AsyncSession, patient_id: uuid.UUID) -> dict[str, ObjectiveEstimate]:
    """One estimate per objective from scored answers since the latest fresh start."""
    reset_at = await resets.cutoff(db, patient_id)
    rows = (
        await db.execute(
            select(Exercise.exercise_type, Exercise.difficulty, ExerciseResponse.outcome)
            .join(ExerciseResponse, ExerciseResponse.exercise_id == Exercise.id)
            .where(
                Exercise.patient_id == patient_id,
                resets.after(ExerciseResponse.created_at, reset_at),
            )
            .order_by(ExerciseResponse.created_at.desc())
            .limit(HISTORY_LIMIT)
        )
    ).all()
    history: dict[str, list[tuple[str, int]]] = {o.value: [] for o in Objective}
    for exercise_type, difficulty, outcome in reversed(rows):
        if (objective := OBJECTIVES.get(exercise_type)) is not None:
            history[objective.value].append((outcome, difficulty))
    return {name: estimate(name, h) for name, h in history.items()}
