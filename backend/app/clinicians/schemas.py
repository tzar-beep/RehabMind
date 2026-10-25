"""Clinician-facing read models. Observed activity only: no scores, risks or prognoses."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class OutcomeCounts(BaseModel):
    correct: int = 0
    near_miss: int = 0
    incorrect: int = 0
    skipped: int = 0

    @property
    def attempted(self) -> int:
        return self.correct + self.near_miss + self.incorrect + self.skipped


class ConstraintBrief(BaseModel):
    version: int
    min_difficulty: int
    max_difficulty: int
    allowed_exercise_types: list[str]
    allowed_response_modes: list[str]


class PatientListItem(BaseModel):
    id: str
    display_name: str
    sessions_completed: int
    last_session_at: datetime | None
    # Last (up to) 20 responses; None when there are none.
    recent_responses: int
    recent_correct: int
    constraints: ConstraintBrief | None


class ModeStats(BaseModel):
    mode: str
    attempted: int
    correct: int


class ResetInfo(BaseModel):
    at: datetime
    by: str | None
    reason: str


class PatientOverview(BaseModel):
    id: str
    display_name: str
    patient_since: datetime
    care_team: list[str]
    sessions_total: int
    sessions_completed: int
    sessions_stopped_early: int
    has_active_session: bool
    first_session_at: datetime | None
    last_session_at: datetime | None
    outcomes: OutcomeCounts
    by_mode: list[ModeStats]
    hinted_responses: int
    median_latency_ms: int | None
    current_working_difficulty: int | None
    # Picture-naming error types (app.analysis.errors), e.g. {"semantic": 4, "formal": 1}.
    error_profile: dict[str, int] = {}
    uncertain_speech_matches: int = 0
    # Recognised matches the patient said were not what they said (speech confirmation).
    speech_misheard: int = 0
    # Patients' after-session ratings: too_easy / just_right / too_hard -> count.
    difficulty_ratings: dict[str, int] = {}
    # Figures above count only practice since this fresh start (None: never reset).
    last_reset: ResetInfo | None = None


class SessionSummary(BaseModel):
    id: str
    started_at: datetime
    completed_at: datetime | None
    status: str
    planned: int
    outcomes: OutcomeCounts
    attempted: int
    avg_difficulty: float | None
    modes: list[str]
    duration_s: int | None
    difficulty_rating: str | None = None
    # Started before the patient's latest progress reset: kept for history, not counted.
    before_reset: bool = False


class SessionPage(BaseModel):
    items: list[SessionSummary]
    total: int
    limit: int
    offset: int
    # Sessions opened and left without an answer, not listed (include_empty=true lists them).
    empty_hidden: int = 0


class SpeechAttempt(BaseModel):
    status: str
    reason: str | None


class TranscriptQuality(BaseModel):
    no_speech_prob: float | None
    avg_logprob: float | None
    low_confidence_words: list[str]


class ExerciseDetail(BaseModel):
    position: int
    issued_at: datetime
    exercise_type: str
    difficulty: int
    source: str
    status: str
    picture: str | None
    category: str | None
    image_url: str | None
    target: str
    prompt: str
    response_mode: str | None
    response_text: str | None
    outcome: str | None
    match_type: str | None
    # Picture naming only: PNT-style error type (app.analysis.errors).
    error_type: str | None = None
    # Speech answer scored correct although the recogniser was unsure of the matched word.
    uncertain_speech_match: bool = False
    hints_used: int | None
    latency_ms: int | None
    transcript_quality: TranscriptQuality | None
    speech_attempts: list[SpeechAttempt]


class SessionDetail(BaseModel):
    session: SessionSummary
    exercises: list[ExerciseDetail]


class TrendPoint(BaseModel):
    session_id: str
    started_at: datetime
    attempted: int
    correct: int
    near_miss: int
    incorrect: int
    skipped: int
    accuracy: float  # correct / attempted, 0..1
    avg_difficulty: float


class ConstraintVersion(BaseModel):
    id: str
    version: int
    is_active: bool
    created_at: datetime
    created_by: str
    note: str | None
    allowed_exercise_types: list[str]
    allowed_response_modes: list[str]
    allowed_categories: list[str] | None
    min_difficulty: int
    max_difficulty: int
    max_exercises_per_session: int
    advance_after_correct: int
    step_back_after_incorrect: int
    progression_mode: str = "step"


class WordProgress(BaseModel):
    """One picture's record across all single-word exercises (naming, completion,
    repetition, recognition, category), since the latest fresh start."""

    picture: str
    word: str
    image_url: str
    category: str
    difficulty: int
    attempts: int
    correct: int
    close: int
    recent: list[str]  # last outcomes, oldest first (at most RECENT_PER_WORD)
    common_error: str | None  # most frequent PNT error type, if any
    last_practised: datetime
    # needs_work: right under half the time (2+ tries); secure: last three right;
    # learning: anything else.
    status: Literal["needs_work", "learning", "secure"]
