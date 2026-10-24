"""Phases 2-3 dry run: simulated participants practise in the real app.

    uv run python -m app.scripts.simulate_participants phase2 [--tag r1] [--seed 11]
    uv run python -m app.scripts.simulate_participants phase3 [--tag r1] [--seed 13]

SYNTHETIC DATA. No person took part. Each simulated participant has a hidden ability and a
hidden difficulty for every picture (from the picture's word frequency, length and BOSS name
agreement, plus personal noise), so the app's own levels are only an approximation of what
is hard for them, as with real people. They practise through the app's session service
(the code the API runs): the app chooses pictures, with the configured AI provider, applies
the clinician's limits, scores the typed answer and moves difficulty. The study lead's mode
switch is a new constraint version before each session, as in the protocols.

Wrong answers are realistic strings, not labels: a word from the same semantic field, a
sound error ("dag"), a description ("you use it to read"), or "I'm not sure". The app scores
and classifies them itself. After each session the participant gives the in-app rating.

What this shows: the study pipeline runs end to end (accounts, mode switching, ratings,
pseudonymised export, analysis) and how the two progression modes behave with learners whose
difficulty differs from the catalogue levels. What it cannot show: anything about real
people. The participants follow the model written here, by construction.

Refuses to run outside local development, like the dev seed. Accounts are named
sim-<phase>-<tag>-NN@study.invalid and can be removed with the admin page.
"""

import argparse
import asyncio
import csv
import json
import math
import random
import secrets
import sys
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from statistics import mean, pstdev

from sqlalchemy import select
from wordfreq import zipf_frequency

from app.analysis.errors import LEXICON_PATH
from app.clinical.service import ConstraintSetIn, create_version
from app.clinicians.models import Clinician, PatientClinician
from app.core.config import get_settings
from app.core.db import SessionLocal
from app.core.passwords import hash_password
from app.exercises.catalog import sync_stimuli
from app.exercises.models import Stimulus
from app.exercises.norms import syllables
from app.exercises.types import ExerciseType, ResponseMode
from app.patients.models import Patient
from app.scripts import study_data
from app.scripts.seed_dev import assert_seed_allowed
from app.sessions import service
from app.users.models import Role, User

ROOT = Path(__file__).parents[3] / "docs" / "validation"
CATALOG = Path(__file__).parents[1] / "exercises" / "stimuli_catalog.json"
BAND = (0.6, 0.9)
# Phase 3: practised categories (allowed in the constraint set) and unpractised controls.
PRACTISED = ["household", "personal", "food", "transport"]
CONTROLS = ["animals", "tools", "music", "nature"]


@dataclass
class Profile:
    name: str
    ability: float  # mean ability (logit); 0 = 50% on an average picture
    spread: float  # between-participant sd of ability
    errors: dict[str, float]  # share of each kind of wrong answer
    item_learning: float = 0.0  # ability gain on a picture each time it is practised
    general_learning: float = 0.0  # gain over the whole treatment, all pictures
    quit_after_errors: float = 0.0  # chance of stopping early after three misses in a row


OLDER_ADULT = Profile(
    "Healthy older adult",
    ability=2.2,
    spread=0.5,
    errors={"no_response": 0.45, "semantic": 0.4, "sound": 0.15},
)
APHASIA = [
    Profile(
        "Anomic aphasia, mild",
        ability=0.9,
        spread=0.3,
        errors={"no_response": 0.35, "semantic": 0.35, "description": 0.25, "sound": 0.05},
        item_learning=0.12,
        general_learning=0.4,
        quit_after_errors=0.05,
    ),
    Profile(
        "Conduction aphasia, moderate",
        ability=0.0,
        spread=0.3,
        errors={"sound": 0.6, "semantic": 0.1, "no_response": 0.3},
        item_learning=0.1,
        general_learning=0.3,
        quit_after_errors=0.1,
    ),
    Profile(
        "Mixed aphasia, moderate-severe",
        ability=-0.9,
        spread=0.3,
        errors={"no_response": 0.5, "semantic": 0.2, "sound": 0.2, "unrelated": 0.1},
        item_learning=0.08,
        general_learning=0.2,
        quit_after_errors=0.2,
    ),
    Profile(
        "Anomic aphasia, moderate",
        ability=0.2,
        spread=0.3,
        errors={"no_response": 0.4, "semantic": 0.4, "description": 0.2},
        item_learning=0.1,
        general_learning=0.3,
        quit_after_errors=0.1,
    ),
]


def picture_difficulty() -> dict[str, float]:
    """True difficulty of each naming photo (logit): rarer, longer and less consistently named
    pictures are harder (Nickels & Howard 1995). Independent of the catalogue's levels."""
    photos = [
        p
        for p in json.loads(CATALOG.read_text(encoding="utf-8"))["photos"]
        if "picture_naming" in p["exercise_types"] and "norms" in p
    ]

    def z(xs: list[float]) -> list[float]:
        m, s = mean(xs), pstdev(xs) or 1.0
        return [(x - m) / s for x in xs]

    freq = z([-zipf_frequency(p["target"], "en") for p in photos])
    length = z([float(syllables(p["target"])) for p in photos])
    agree = z([-p["norms"]["name_agreement"] for p in photos])
    return {
        p["slug"]: 0.8 * f + 0.4 * n + 0.6 * a
        for p, f, n, a in zip(photos, freq, length, agree, strict=True)
    }


@dataclass
class Participant:
    code: str
    profile: Profile
    ability: float
    item_noise: dict[str, float]
    practice: dict[str, int] = field(default_factory=dict)
    progress: float = 0.0  # 0 at the start of treatment, 1 at the end

    def p_correct(self, slug: str, base: dict[str, float]) -> float:
        theta = (
            self.ability
            + self.profile.general_learning * self.progress
            + self.profile.item_learning * min(self.practice.get(slug, 0), 8)
        )
        return 1 / (1 + math.exp(-(theta - base[slug] - self.item_noise[slug])))


class Answers:
    """Realistic wrong answers for a target word."""

    def __init__(self) -> None:
        lex = json.loads(LEXICON_PATH.read_text(encoding="utf-8"))
        self.fields: dict[str, list[str]] = lex["fields"]
        self.associates: dict[str, list[str]] = lex["associates"]
        self.words = sorted({w for ws in self.fields.values() for w in ws})

    def wrong(self, kind: str, target: str, accepted: set[str], rng: random.Random) -> str | None:
        if kind == "semantic":
            near = [
                w
                for ws in self.fields.values()
                if target in ws
                for w in ws
                if w not in accepted and w != target
            ]
            if near:
                return rng.choice(near)
            kind = "no_response"
        if kind == "description" and self.associates.get(target):
            return f"you use it to {rng.choice(self.associates[target])}"
        if kind in ("sound", "description"):
            return sound_error(target, rng)
        if kind == "unrelated":
            return rng.choice([w for w in self.words if w not in accepted and w != target])
        return None  # no response: the participant presses "I'm not sure"


def sound_error(word: str, rng: random.Random) -> str:
    """A phonological slip: change one letter (vowel for vowel, consonant for consonant)."""
    vowels, consonants = "aeiou", "bcdfghklmnprstvw"
    letters = list(word.split()[0])
    i = rng.randrange(len(letters))
    pool = vowels if letters[i] in vowels else consonants
    letters[i] = rng.choice([c for c in pool if c != letters[i]])
    return "".join(letters)


def rating(accuracy: float, rng: random.Random) -> str:
    """The participant's own "how did that feel": mostly from session accuracy, with noise."""
    felt = accuracy + rng.gauss(0, 0.08)
    return "too_easy" if felt > 0.92 else "too_hard" if felt < 0.55 else "just_right"


async def make_accounts(db, phase: str, tag: str, n: int) -> tuple[User, list[Patient]]:
    password = hash_password(secrets.token_urlsafe(24))  # nobody signs in to these
    prefix = f"sim-{phase}-{tag}"
    if await db.scalar(select(User).where(User.email.like(f"{prefix}-%"))):
        sys.exit(f"accounts {prefix}-* exist already; choose another --tag")
    lead = User(
        email=f"{prefix}-lead@study.invalid",
        role=Role.CLINICIAN,
        display_name=f"Study lead ({phase}, simulated)",
        password_hash=password,
    )
    db.add(lead)
    await db.flush()
    clinician = Clinician(user_id=lead.id)
    db.add(clinician)
    patients = []
    for i in range(1, n + 1):
        user = User(
            email=f"{prefix}-{i:02d}@study.invalid",
            role=Role.PATIENT,
            display_name=f"Simulated {phase} {i:02d}",
            password_hash=password,
        )
        db.add(user)
        await db.flush()
        patient = Patient(user_id=user.id)
        db.add(patient)
        await db.flush()
        db.add(PatientClinician(patient_id=patient.id, clinician_id=clinician.id))
        patients.append(patient)
    await db.commit()
    return lead, patients


def plan(mode: str, per_session: int, categories: list[str] | None) -> ConstraintSetIn:
    return ConstraintSetIn(
        allowed_exercise_types=[ExerciseType.PICTURE_NAMING],
        allowed_response_modes=[ResponseMode.TEXT],
        allowed_categories=categories,
        min_difficulty=1,
        max_difficulty=5,
        max_exercises_per_session=per_session,
        progression_mode=mode,
        note=f"Simulated study: {mode} mode",
    )


async def run_session(
    db, patient: Patient, user_id: uuid.UUID, who: Participant, mode: str, base, answers, rng, log
) -> dict:
    session = await service.start_or_resume(db, patient.id, user_id)
    results, streak = [], 0
    while True:
        exercise = await service.pending_exercise(db, session.id)
        if exercise is None:
            break
        stim = await db.get(Stimulus, exercise.stimulus_id)
        p = who.p_correct(stim.slug, base)
        hints = 0
        if p < 0.5 and rng.random() < 0.4:  # struggling: ask for a hint or two
            hints = 1 + (rng.random() < 0.5)
            p = min(0.95, p + 0.12 * hints)
        accepted = {a.lower() for a in exercise.expected.get("accepted_answers", [])}
        target = exercise.expected["target"]
        if rng.random() < p:
            text = target
        else:
            kinds = list(who.profile.errors)
            kind = rng.choices(kinds, [who.profile.errors[k] for k in kinds])[0]
            text = answers.wrong(kind, target, accepted | {target}, rng)
        latency = int(rng.lognormvariate(math.log(4000 + 6000 * (1 - p)), 0.35))
        _, result, session = await service.submit_response(
            db, patient.id, exercise.id, text, latency, hints_used=hints
        )
        who.practice[stim.slug] = who.practice.get(stim.slug, 0) + 1
        ok = result.outcome == "correct"
        results.append(ok)
        log.append(
            {
                "participant": who.code,
                "mode": mode,
                "session": str(session.id),
                "slug": stim.slug,
                "level": exercise.difficulty,
                "true_p": round(p, 3),
                "outcome": result.outcome,
            }
        )
        streak = 0 if ok else streak + 1
        if streak >= 3 and rng.random() < who.profile.quit_after_errors:
            await service.end_session(db, patient.id)  # "Stop for today"
            await db.commit()
            break
    await db.refresh(session)
    felt = ""
    if session.status != "active" and results:
        felt = session.difficulty_rating = rating(mean(results), rng)
        await db.commit()
    return {"answers": len(results), "stopped_early": session.status == "ended", "rating": felt}


def probe(who: Participant, base: dict[str, float], slugs: list[str], rng) -> float:
    """SLP-scored naming probe on paper: no hints, no feedback, no practice effect."""
    return mean(rng.random() < who.p_correct(s, base) for s in slugs)


async def run(phase: str, tag: str, seed: int) -> None:
    rng = random.Random(seed)  # noqa: S311 - simulation, not security
    base = picture_difficulty()
    answers = Answers()
    phase3 = phase == "phase3"
    n, sessions, per_session = (len(APHASIA), 24, 20) if phase3 else (12, 8, 10)
    async with SessionLocal() as db:
        await sync_stimuli(db)
        cats = {s.slug: s.category for s in (await db.execute(select(Stimulus))).scalars().all()}
        lead, patients = await make_accounts(db, phase, tag, n)
        people, schedules = [], []
        for i in range(n):
            profile = APHASIA[i] if phase3 else OLDER_ADULT
            people.append(
                Participant(
                    code=f"{phase}-{i + 1:02d}",
                    profile=profile,
                    ability=rng.gauss(profile.ability, profile.spread),
                    item_noise={s: rng.gauss(0, 0.4) for s in base},
                )
            )
            if phase3:  # alternating treatments, random order within pairs of sessions
                order = []
                for _ in range(sessions // 2):
                    order += rng.sample(["step", "ability"], 2)
            else:  # ABBA or BAAB, counterbalanced across participants
                a, b = ("step", "ability") if i % 2 == 0 else ("ability", "step")
                order = [a, b, b, a, b, a, a, b]
            schedules.append(order)

        practised = [s for s in base if cats.get(s) in PRACTISED]
        controls = [s for s in base if cats.get(s) in CONTROLS]
        probes: list[dict] = []
        log: list[dict] = []
        sessions_done = []
        for patient, who, order in zip(patients, people, schedules, strict=True):
            user_id = patient.user_id
            if phase3:
                for b in range(3):
                    probes.append(
                        _probe_row(who, "baseline", b + 1, base, practised, controls, rng)
                    )
            for s, mode in enumerate(order):
                who.progress = s / len(order)
                if phase3 and rng.random() < 0.1:  # a missed session (adherence)
                    sessions_done.append({"participant": who.code, "mode": mode, "done": False})
                    continue
                await create_version(
                    db, patient.id, plan(mode, per_session, PRACTISED if phase3 else None), lead.id
                )
                await db.commit()
                out = await run_session(db, patient, user_id, who, mode, base, answers, rng, log)
                sessions_done.append({"participant": who.code, "mode": mode, "done": True, **out})
                if phase3 and (s + 1) % 4 == 0:  # weekly probe
                    probes.append(
                        _probe_row(who, "treatment", (s + 1) // 4, base, practised, controls, rng)
                    )
            if phase3:
                who.progress = 1.0
                probes.append(_probe_row(who, "post", 1, base, practised, controls, rng))
                who.practice = {s: max(0, c - 3) for s, c in who.practice.items()}  # some decay
                probes.append(_probe_row(who, "maintenance", 1, base, practised, controls, rng))
            print(f"{who.code} ({who.profile.name}): done", flush=True)

        ids = [str(p.id) for p in patients]
    out_dir = ROOT / "simulated" / phase
    out_dir.mkdir(parents=True, exist_ok=True)
    export = out_dir / "study.csv"
    # The pseudonym key is irrelevant for synthetic data; a fixed salt keeps files stable.
    await study_data.export(f"simulated-{tag}", export, ids)
    _write(out_dir / "true-difficulty.csv", log)
    _write(out_dir / "sessions.csv", sessions_done)
    if probes:
        _write(out_dir / "probes.csv", probes)
    report = study_data.analyse(export)
    report += "\n" + summary(log, sessions_done, probes, people)
    (ROOT / "results" / f"{phase}-simulated.md").write_text(
        f"<!-- SYNTHETIC: simulated participants, not study data. See ../simulated.md -->\n"
        f"{report}",
        encoding="utf-8",
    )
    print(report)


def _probe_row(who, phase_name, number, base, practised, controls, rng) -> dict:
    return {
        "participant": who.code,
        "phase": phase_name,
        "probe": number,
        "practised": round(probe(who, base, practised, rng), 3),
        "control": round(probe(who, base, controls, rng), 3),
    }


def _write(path: Path, rows: list[dict]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def summary(log, sessions_done, probes, people) -> str:
    lines = [
        "## Summary across simulated participants",
        "",
        "Productive band here uses each simulated participant's *true* chance of success "
        "(known only because they are simulated); the table above uses the app's estimate.",
        "",
        "| Mode | Sessions | Answers | Accuracy | True chance in productive band | "
        "Too hard (< 50%) | Sessions rated just right |",
        "|---|---|---|---|---|---|---|",
    ]
    for mode in ("step", "ability"):
        answered = [t for t in log if t["mode"] == mode]
        done = [s for s in sessions_done if s["mode"] == mode and s["done"]]
        rated = [s["rating"] for s in done if s["rating"]]
        if not answered:
            continue
        just = sum(r == "just_right" for r in rated)
        lines.append(
            f"| {mode} | {len(done)} | {len(answered)} | "
            f"{mean(t['outcome'] == 'correct' for t in answered):.0%} | "
            f"{mean(BAND[0] <= t['true_p'] <= BAND[1] for t in answered):.0%} | "
            f"{mean(t['true_p'] < 0.5 for t in answered):.0%} | "
            f"{just}/{len(rated)} ({just / len(rated) if rated else 0:.0%}) |"
        )
    done = [s for s in sessions_done if s["done"]]
    lines += [
        "",
        f"Sessions: {len(done)} of {len(sessions_done)} planned were done; "
        f"{sum(s['stopped_early'] for s in done)} stopped early.",
    ]
    if probes:
        lines += [
            "",
            "## Naming probes (phase 3)",
            "",
            "Practised = pictures in the practised categories; control = unpractised "
            "categories. Each value is the mean probe accuracy for that phase.",
            "",
            "| Participant | Profile | Baseline practised | Post practised | Maintenance "
            "practised | Baseline control | Post control | NAP baseline→treatment (practised) |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for who in people:
            ps = [p for p in probes if p["participant"] == who.code]

            def m(phase_name: str, key: str, ps=ps) -> float:
                return mean(p[key] for p in ps if p["phase"] == phase_name)

            effect = study_data.nap(
                [p["practised"] for p in ps if p["phase"] == "baseline"],
                [p["practised"] for p in ps if p["phase"] == "treatment"],
            )
            lines.append(
                f"| {who.code} | {who.profile.name} | {m('baseline', 'practised'):.0%} | "
                f"{m('post', 'practised'):.0%} | {m('maintenance', 'practised'):.0%} | "
                f"{m('baseline', 'control'):.0%} | {m('post', 'control'):.0%} | {effect:.2f} |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("phase", choices=["phase2", "phase3"])
    ap.add_argument("--tag", default="r1")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()
    try:
        assert_seed_allowed(get_settings())
    except RuntimeError as e:
        sys.exit(str(e))
    seed = args.seed if args.seed is not None else (11 if args.phase == "phase2" else 13)
    asyncio.run(run(args.phase, args.tag, seed))


if __name__ == "__main__":
    main()
