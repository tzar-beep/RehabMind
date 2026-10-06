"""Server-side aggregation of stored practice data for clinicians.

Callers must have already authorized access to the patient(s) via `app.patients.access`.
All queries are bounded (aggregates, LIMIT, or pagination).
"""

import uuid
from collections import defaultdict

from sqlalchemy import Integer, case, cast, func, select
from sqlalchemy.dialects.postgresql import distinct_on
from sqlalchemy.ext.asyncio import AsyncSession

from app.clinical.models import ConstraintSet
from app.clinicians.models import Clinician, PatientClinician
from app.clinicians.schemas import (
    ConstraintBrief,
    ExerciseDetail,
    ModeStats,
    OutcomeCounts,
    PatientListItem,
    PatientOverview,
    ResetInfo,
    SessionDetail,
    SessionSummary,
    SpeechAttempt,
    TranscriptQuality,
    TrendPoint,
)
from app.exercises.models import Exercise, Stimulus
from app.patients.models import Patient
from app.performance.models import PerformanceProfile
from app.sessions import resets
from app.sessions.models import ExerciseResponse, PracticeSession
from app.speech.models import AudioAsset
from app.users.models import User

RECENT_WINDOW = 20
TREND_SESSIONS = 20


def _brief(cs: ConstraintSet | None) -> ConstraintBrief | None:
    if cs is None:
        return None
    return ConstraintBrief(
        version=cs.version,
        min_difficulty=cs.min_difficulty,
        max_difficulty=cs.max_difficulty,
        allowed_exercise_types=cs.allowed_exercise_types,
        allowed_response_modes=cs.allowed_response_modes,
    )


async def latest_constraints_for(
    db: AsyncSession, patient_ids: list[uuid.UUID]
) -> dict[uuid.UUID, ConstraintSet]:
    if not patient_ids:
        return {}
    rows = await db.execute(
        select(ConstraintSet)
        .where(ConstraintSet.patient_id.in_(patient_ids))
        .ext(distinct_on(ConstraintSet.patient_id))
        .order_by(ConstraintSet.patient_id, ConstraintSet.version.desc())
    )
    return {cs.patient_id: cs for cs in rows.scalars()}


async def patient_list(db: AsyncSession, patients: list[Patient]) -> list[PatientListItem]:
    ids = [p.id for p in patients]
    if not ids:
        return []
    cut = resets.cutoffs_subquery()
    sessions = {
        pid: (completed, last)
        for pid, completed, last in (
            await db.execute(
                select(
                    PracticeSession.patient_id,
                    func.count().filter(PracticeSession.status == "completed"),
                    func.max(PracticeSession.started_at),
                )
                .outerjoin(cut, cut.c.patient_id == PracticeSession.patient_id)
                .where(
                    PracticeSession.patient_id.in_(ids),
                    resets.since(PracticeSession.started_at, cut.c.reset_at),
                )
                .group_by(PracticeSession.patient_id)
            )
        ).all()
    }
    ranked = (
        select(
            ExerciseResponse.patient_id,
            ExerciseResponse.outcome,
            func.row_number()
            .over(
                partition_by=ExerciseResponse.patient_id,
                order_by=ExerciseResponse.created_at.desc(),
            )
            .label("rn"),
        )
        .outerjoin(cut, cut.c.patient_id == ExerciseResponse.patient_id)
        .where(
            ExerciseResponse.patient_id.in_(ids),
            resets.since(ExerciseResponse.created_at, cut.c.reset_at),
        )
        .subquery()
    )
    recent = {
        pid: (n, correct)
        for pid, n, correct in (
            await db.execute(
                select(
                    ranked.c.patient_id,
                    func.count(),
                    func.count().filter(ranked.c.outcome == "correct"),
                )
                .where(ranked.c.rn <= RECENT_WINDOW)
                .group_by(ranked.c.patient_id)
            )
        ).all()
    }
    constraints = await latest_constraints_for(db, ids)
    return [
        PatientListItem(
            id=str(p.id),
            display_name=p.user.display_name,
            sessions_completed=sessions.get(p.id, (0, None))[0],
            last_session_at=sessions.get(p.id, (0, None))[1],
            recent_responses=recent.get(p.id, (0, 0))[0],
            recent_correct=recent.get(p.id, (0, 0))[1],
            constraints=_brief(constraints.get(p.id)),
        )
        for p in patients
    ]


async def overview(db: AsyncSession, patient: Patient) -> PatientOverview:
    pid = patient.id
    last_reset = await resets.latest_reset(db, pid)
    reset_at = last_reset.created_at if last_reset else None
    sessions_since = (PracticeSession.patient_id == pid) & resets.after(
        PracticeSession.started_at, reset_at
    )
    responses_since = (ExerciseResponse.patient_id == pid) & resets.after(
        ExerciseResponse.created_at, reset_at
    )
    s_total, s_completed, s_ended, s_active, first, last = (
        await db.execute(
            select(
                func.count(),
                func.count().filter(PracticeSession.status == "completed"),
                func.count().filter(PracticeSession.status == "ended"),
                func.count().filter(PracticeSession.status == "active"),
                func.min(PracticeSession.started_at),
                func.max(PracticeSession.started_at),
            ).where(sessions_since)
        )
    ).one()

    outcomes = OutcomeCounts()
    by_mode: dict[str, list[int]] = defaultdict(lambda: [0, 0])
    for mode, outcome, n in (
        await db.execute(
            select(ExerciseResponse.mode, ExerciseResponse.outcome, func.count())
            .where(responses_since)
            .group_by(ExerciseResponse.mode, ExerciseResponse.outcome)
        )
    ).all():
        setattr(outcomes, outcome, getattr(outcomes, outcome) + n)
        by_mode[mode][0] += n
        by_mode[mode][1] += n if outcome == "correct" else 0

    hinted, median = (
        await db.execute(
            select(
                func.count().filter(
                    cast(ExerciseResponse.analysis["hints_used"].astext, Integer) > 0
                ),
                func.percentile_cont(0.5)
                .within_group(ExerciseResponse.latency_ms)
                .filter(ExerciseResponse.outcome != "skipped"),
            ).where(responses_since)
        )
    ).one()

    care_team = (
        await db.execute(
            select(User.display_name)
            .join(Clinician, Clinician.user_id == User.id)
            .join(PatientClinician, PatientClinician.clinician_id == Clinician.id)
            .where(PatientClinician.patient_id == pid)
            .order_by(User.display_name)
        )
    ).scalars()
    level = await db.scalar(
        select(PerformanceProfile.target_difficulty).where(PerformanceProfile.patient_id == pid)
    )
    return PatientOverview(
        id=str(pid),
        display_name=patient.user.display_name,
        patient_since=patient.created_at,
        care_team=list(care_team),
        sessions_total=s_total,
        sessions_completed=s_completed,
        sessions_stopped_early=s_ended,
        has_active_session=s_active > 0,
        first_session_at=first,
        last_session_at=last,
        outcomes=outcomes,
        by_mode=[
            ModeStats(mode=m, attempted=a, correct=c) for m, (a, c) in sorted(by_mode.items())
        ],
        hinted_responses=hinted,
        median_latency_ms=int(median) if median is not None else None,
        current_working_difficulty=level,
        last_reset=ResetInfo(
            at=last_reset.created_at,
            by=await db.scalar(select(User.display_name).where(User.id == last_reset.reset_by)),
            reason=last_reset.reason,
        )
        if last_reset
        else None,
    )


def _session_aggregates():
    """Per-session counts computed in SQL (one row per session)."""
    return (
        select(
            Exercise.session_id.label("session_id"),
            func.count(ExerciseResponse.id).label("attempted"),
            func.count().filter(ExerciseResponse.outcome == "correct").label("correct"),
            func.count().filter(ExerciseResponse.outcome == "near_miss").label("near_miss"),
            func.count().filter(ExerciseResponse.outcome == "incorrect").label("incorrect"),
            func.count().filter(ExerciseResponse.outcome == "skipped").label("skipped"),
            func.avg(case((ExerciseResponse.id.isnot(None), Exercise.difficulty))).label(
                "avg_difficulty"
            ),
            func.array_remove(func.array_agg(func.distinct(ExerciseResponse.mode)), None).label(
                "modes"
            ),
        )
        .join(ExerciseResponse, ExerciseResponse.exercise_id == Exercise.id, isouter=True)
        .group_by(Exercise.session_id)
        .subquery()
    )


def _summary(s: PracticeSession, agg, reset_at=None) -> SessionSummary:
    duration = int((s.completed_at - s.started_at).total_seconds()) if s.completed_at else None
    return SessionSummary(
        id=str(s.id),
        started_at=s.started_at,
        completed_at=s.completed_at,
        status=s.status,
        planned=s.planned_exercises,
        outcomes=OutcomeCounts(
            correct=agg.correct if agg else 0,
            near_miss=agg.near_miss if agg else 0,
            incorrect=agg.incorrect if agg else 0,
            skipped=agg.skipped if agg else 0,
        ),
        attempted=agg.attempted if agg else 0,
        avg_difficulty=round(float(agg.avg_difficulty), 2)
        if agg and agg.avg_difficulty is not None
        else None,
        modes=sorted(agg.modes or []) if agg else [],
        duration_s=duration,
        before_reset=reset_at is not None and s.started_at < reset_at,
    )


async def sessions_page(
    db: AsyncSession, patient_id: uuid.UUID, limit: int, offset: int
) -> tuple[list[SessionSummary], int]:
    agg = _session_aggregates()
    reset_at = await resets.cutoff(db, patient_id)
    total = await db.scalar(select(func.count()).where(PracticeSession.patient_id == patient_id))
    rows = await db.execute(
        select(PracticeSession, agg)
        .join(agg, agg.c.session_id == PracticeSession.id, isouter=True)
        .where(PracticeSession.patient_id == patient_id)
        .order_by(PracticeSession.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return [_summary(r[0], r, reset_at) for r in rows.all()], total or 0


async def trends(db: AsyncSession, patient_id: uuid.UUID) -> list[TrendPoint]:
    """Most recent sessions with at least one response, oldest first."""
    agg = _session_aggregates()
    reset_at = await resets.cutoff(db, patient_id)
    rows = (
        await db.execute(
            select(PracticeSession.id, PracticeSession.started_at, agg)
            .join(agg, agg.c.session_id == PracticeSession.id)
            .where(
                PracticeSession.patient_id == patient_id,
                agg.c.attempted > 0,
                resets.after(PracticeSession.started_at, reset_at),
            )
            .order_by(PracticeSession.started_at.desc())
            .limit(TREND_SESSIONS)
        )
    ).all()
    return [
        TrendPoint(
            session_id=str(r.id),
            started_at=r.started_at,
            attempted=r.attempted,
            correct=r.correct,
            near_miss=r.near_miss,
            incorrect=r.incorrect,
            skipped=r.skipped,
            accuracy=round(r.correct / r.attempted, 3),
            avg_difficulty=round(float(r.avg_difficulty), 2),
        )
        for r in reversed(rows)
    ]


async def session_detail(
    db: AsyncSession, patient_id: uuid.UUID, session_id: uuid.UUID
) -> SessionDetail | None:
    session = await db.get(PracticeSession, session_id)
    if session is None or session.patient_id != patient_id:
        return None
    reset_at = await resets.cutoff(db, patient_id)
    agg = _session_aggregates()
    agg_row = (await db.execute(select(agg).where(agg.c.session_id == session_id))).first()

    rows = (
        await db.execute(
            select(Exercise, ExerciseResponse, Stimulus)
            .join(ExerciseResponse, ExerciseResponse.exercise_id == Exercise.id, isouter=True)
            .join(Stimulus, Stimulus.id == Exercise.stimulus_id, isouter=True)
            .where(Exercise.session_id == session_id)
            .order_by(Exercise.position)
        )
    ).all()
    attempts: dict[uuid.UUID, list[SpeechAttempt]] = defaultdict(list)
    # Lifecycle status only: object keys and audio are never selected.
    for exercise_id, status, reason in (
        await db.execute(
            select(AudioAsset.exercise_id, AudioAsset.status, AudioAsset.failure_reason)
            .join(Exercise, Exercise.id == AudioAsset.exercise_id)
            .where(Exercise.session_id == session_id)
            .order_by(AudioAsset.created_at)
        )
    ).all():
        attempts[exercise_id].append(SpeechAttempt(status=status, reason=reason))

    exercises = []
    for ex, resp, stim in rows:
        stt = (resp.analysis or {}).get("stt") if resp else None
        exercises.append(
            ExerciseDetail(
                position=ex.position,
                issued_at=ex.issued_at,
                exercise_type=ex.exercise_type,
                difficulty=ex.difficulty,
                source=ex.source,
                status=ex.status,
                picture=stim.slug if stim else None,
                category=stim.category if stim else None,
                image_url=ex.content.get("image_url"),
                target=ex.expected["target"],
                prompt=ex.content["prompt"],
                response_mode=resp.mode if resp else None,
                response_text=resp.text if resp else None,
                outcome=resp.outcome if resp else None,
                match_type=resp.analysis.get("match_type") if resp else None,
                hints_used=resp.analysis.get("hints_used") if resp else None,
                latency_ms=resp.latency_ms if resp else None,
                transcript_quality=TranscriptQuality(
                    no_speech_prob=stt.get("no_speech_prob"),
                    avg_logprob=stt.get("avg_logprob"),
                    low_confidence_words=stt.get("low_confidence_words") or [],
                )
                if stt
                else None,
                speech_attempts=attempts.get(ex.id, []),
            )
        )
    return SessionDetail(session=_summary(session, agg_row, reset_at), exercises=exercises)
