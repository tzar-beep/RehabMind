"""Phases 2-3: pseudonymised export of practice data, and the per-participant analysis.

    uv run python -m app.scripts.study_data export --salt <secret> --out study.csv \
        [--patients <uuid> ...]
    uv run python -m app.scripts.study_data analyse study.csv [--write]

Export: one row per scored answer. Participants appear only as an HMAC pseudonym keyed by a
study secret held by the study lead (never in the repository), so the file can be shared
with an analyst without names, emails or account IDs. Dates are converted to study day
(days since the participant's first answer). Free-text answers are not exported.

Analysis: for each participant, compares sessions run under each progression mode (the
condition is read from the constraint-set version the exercise was issued under, so an
alternating-treatments design only needs the clinician to switch modes between sessions).
Reports accuracy, the share of answers in the productive band (60-90% predicted success
from the running ability estimate), error runs, and NAP (non-overlap of all pairs) between
conditions on session accuracy. Protocol: docs/validation/protocols/phase3-single-case.md.
"""

import argparse
import asyncio
import csv
import hashlib
import hmac
import sys
import uuid
from collections import defaultdict
from pathlib import Path
from statistics import mean

from sqlalchemy import select

from app.clinical.models import ConstraintSet
from app.core.db import SessionLocal
from app.exercises.models import Exercise, Stimulus
from app.performance.ability import fit, p_success
from app.sessions.models import ExerciseResponse, PracticeSession

REPORT = Path(__file__).parents[3] / "docs" / "validation" / "results" / "study.md"
BAND = (0.6, 0.9)
FIELDS = [
    "participant",
    "study_day",
    "session",
    "position",
    "condition",
    "exercise_type",
    "item",
    "difficulty",
    "mode",
    "outcome",
    "error_type",
    "hints_used",
    "latency_ms",
    "session_rating",
]


def pseudonym(salt: str, patient_id: uuid.UUID) -> str:
    return "P-" + hmac.new(salt.encode(), patient_id.bytes, hashlib.sha256).hexdigest()[:10]


async def export(salt: str, out: Path, patients: list[str]) -> int:
    stmt = (
        select(
            ExerciseResponse,
            Exercise,
            ConstraintSet.progression_mode,
            Stimulus.slug,
            PracticeSession.difficulty_rating,
        )
        .join(Exercise, Exercise.id == ExerciseResponse.exercise_id)
        .join(PracticeSession, PracticeSession.id == Exercise.session_id)
        .join(ConstraintSet, ConstraintSet.id == Exercise.constraint_set_id)
        .join(Stimulus, Stimulus.id == Exercise.stimulus_id, isouter=True)
        .order_by(ExerciseResponse.patient_id, ExerciseResponse.created_at)
    )
    if patients:
        stmt = stmt.where(ExerciseResponse.patient_id.in_([uuid.UUID(p) for p in patients]))
    async with SessionLocal() as db:
        rows = (await db.execute(stmt)).all()
    first: dict[uuid.UUID, object] = {}
    sessions: dict[uuid.UUID, dict[uuid.UUID, int]] = defaultdict(dict)
    with out.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for resp, ex, mode, slug, rating in rows:
            start = first.setdefault(resp.patient_id, resp.created_at)
            numbering = sessions[resp.patient_id]
            numbering.setdefault(ex.session_id, len(numbering) + 1)
            w.writerow(
                {
                    "participant": pseudonym(salt, resp.patient_id),
                    "study_day": (resp.created_at - start).days,
                    "session": numbering[ex.session_id],
                    "position": ex.position,
                    "condition": mode,
                    "exercise_type": ex.exercise_type,
                    "item": slug or "",
                    "difficulty": ex.difficulty,
                    "mode": resp.mode,
                    "outcome": resp.outcome,
                    "error_type": (resp.analysis or {}).get("error_type", ""),
                    "hints_used": (resp.analysis or {}).get("hints_used", 0),
                    "latency_ms": resp.latency_ms or "",
                    "session_rating": rating or "",
                }
            )
    return len(rows)


def nap(a: list[float], b: list[float]) -> float | None:
    """Non-overlap of all pairs (Parker & Vannest 2009): P(value in b > value in a), ties
    counted half. 0.5 = no difference; above 0.5 favours b."""
    if not a or not b:
        return None
    wins = sum((y > x) + 0.5 * (y == x) for x in a for y in b)
    return wins / (len(a) * len(b))


def just_right(rated: dict[str, str]) -> str:
    if not rated:
        return "—"
    n = sum(v == "just_right" for v in rated.values())
    return f"{n}/{len(rated)}"


def analyse(path: Path) -> str:
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    by_person: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        by_person[r["participant"]].append(r)
    lines = [
        "# Study data: per-participant results",
        "",
        f"Generated by `app.scripts.study_data analyse` from `{path.name}` ({len(rows)} "
        "answers). Protocol: [phase3-single-case.md](../protocols/phase3-single-case.md).",
        "",
        "| Participant | Condition | Sessions | Answers | Accuracy | In productive band | "
        "Error runs | Rated just right | NAP vs step (session accuracy) |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for person, rs in sorted(by_person.items()):
        history: dict[str, list[tuple[str, int]]] = defaultdict(list)
        stats: dict[str, dict] = defaultdict(
            lambda: {"answers": 0, "correct": 0, "band": 0, "runs": 0, "sessions": {}, "rated": {}}
        )
        streak = 0
        for r in rs:
            hist = history[r["exercise_type"]]
            p = p_success(fit(hist), int(r["difficulty"])) if hist else None
            s = stats[r["condition"]]
            ok = r["outcome"] == "correct"
            s["answers"] += 1
            s["correct"] += ok
            s["band"] += p is not None and BAND[0] <= p <= BAND[1]
            streak = 0 if ok else streak + 1
            s["runs"] += streak == 3
            s["sessions"].setdefault(r["session"], []).append(ok)
            if r.get("session_rating"):
                s["rated"][r["session"]] = r["session_rating"]
            hist.append((r["outcome"], int(r["difficulty"])))
        session_acc = {c: [mean(v) for v in s["sessions"].values()] for c, s in stats.items()}
        for cond, s in sorted(stats.items()):
            effect = nap(session_acc.get("step", []), session_acc[cond]) if cond != "step" else None
            lines.append(
                f"| {person} | {cond} | {len(s['sessions'])} | {s['answers']} | "
                f"{s['correct'] / s['answers']:.0%} | {s['band'] / s['answers']:.0%} | "
                f"{s['runs']} | {just_right(s['rated'])} | "
                f"{'—' if effect is None else f'{effect:.2f}'} |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="command", required=True)
    ex = sub.add_parser("export")
    ex.add_argument("--salt", required=True, help="study secret; keep it out of the repo")
    ex.add_argument("--out", type=Path, required=True)
    ex.add_argument("--patients", nargs="*", default=[])
    an = sub.add_parser("analyse")
    an.add_argument("path", type=Path)
    an.add_argument("--write", action="store_true")
    args = ap.parse_args()
    if args.command == "export":
        n = asyncio.run(export(args.salt, args.out, args.patients))
        print(f"exported {n} answers to {args.out}")
    else:
        report = analyse(args.path)
        print(report)
        if args.write:
            REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
