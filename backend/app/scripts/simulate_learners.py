"""Phase 0 simulation: does the progression rule keep practice at a productive difficulty?

    uv run python -m app.scripts.simulate_learners [--write] [--learners 300] [--seed 7]

Synthetic learners answer exercises with a known probability of success. Four difficulty
policies are compared on the share of exercises a learner meets in the *productive band*
(true chance of success 60-90%), and on time spent at frustrating or trivial difficulty:

  fixed-easy    always the clinician's minimum level (no personalization)
  fixed-middle  always the middle of the range (one size fits all)
  step-rule     RehabMind today: app.performance.progression.apply_outcome, unchanged
  step+ability  progression_mode "ability": after MIN_ANSWERS_FOR_ABILITY answers, the
                level the learned ability estimate predicts closest to 80% success
                (app.performance.progression.ability_guided_level, the code the app runs)

This is evidence about the algorithm, not about patients: the learners follow a logistic
model by construction. It shows whether personalization *can* keep practice in a useful
band, which is the claim a patient study would then test (docs/validation/personalization.md).
Scenarios vary ability, its drift over time, how wrong the app's model of difficulty is,
and how narrow the clinician's range is.
"""

import math
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from types import SimpleNamespace

from app.performance.ability import HISTORY_LIMIT, fit
from app.performance.progression import (
    MIN_ANSWERS_FOR_ABILITY,
    ability_guided_level,
    apply_outcome,
)

REPORT = Path(__file__).parents[3] / "docs" / "validation" / "results" / "simulation.md"
BAND = (0.6, 0.9)
TOO_HARD = 0.5
TOO_EASY = 0.95
TRIALS = 300  # about 15 sessions of 20 exercises
FRUSTRATION_STREAK = 3


@dataclass(frozen=True)
class Scenario:
    name: str
    drift: float = 0.0  # change in true ability over all trials
    slope: float = 0.8  # true difficulty step in ability units (the app assumes 0.8)
    item_noise: float = 0.0  # sd of per-item difficulty around its level
    min_level: int = 1
    max_level: int = 5


SCENARIOS = [
    Scenario("Stable ability, model correct"),
    Scenario("Improving (+1.5 over the period)", drift=1.5),
    Scenario("Declining (-1.0 over the period)", drift=-1.0),
    Scenario("Levels steeper than assumed (slope 1.2)", slope=1.2),
    Scenario("Noisy items (sd 0.6 within a level)", item_noise=0.6),
    Scenario("Narrow clinician range (levels 2-3)", min_level=2, max_level=3),
]
POLICIES = ["fixed-easy", "fixed-middle", "step-rule", "step+ability"]


def true_p(theta: float, level: int, sc: Scenario, rng: random.Random) -> float:
    d = sc.slope * (level - 3) + rng.gauss(0, sc.item_noise)
    return 1 / (1 + math.exp(-(theta - d)))


def run_learner(theta0: float, policy: str, sc: Scenario, rng: random.Random) -> dict:
    cs = SimpleNamespace(
        min_difficulty=sc.min_level,
        max_difficulty=sc.max_level,
        advance_after_correct=3,
        step_back_after_incorrect=2,
    )
    profile = SimpleNamespace(
        target_difficulty=sc.min_level,
        consecutive_correct=0,
        consecutive_incorrect=0,
        total_attempts=0,
        total_correct=0,
        recent_outcomes=[],
    )
    history: list[tuple[str, int]] = []
    ps, correct, streak, frustrations = [], 0, 0, 0
    for t in range(TRIALS):
        theta = theta0 + sc.drift * t / TRIALS
        if policy == "fixed-easy":
            level = sc.min_level
        elif policy == "fixed-middle":
            level = (sc.min_level + sc.max_level + 1) // 2
        elif policy == "step-rule" or len(history) < MIN_ANSWERS_FOR_ABILITY:
            level = profile.target_difficulty
        else:
            level = ability_guided_level(fit(history[-HISTORY_LIMIT:]), cs)
        p = true_p(theta, level, sc, rng)
        ok = rng.random() < p
        outcome = "correct" if ok else "incorrect"
        apply_outcome(profile, outcome, cs)
        history.append((outcome, level))
        ps.append(p)
        correct += ok
        streak = 0 if ok else streak + 1
        frustrations += streak == FRUSTRATION_STREAK
    return {
        "in_band": mean(BAND[0] <= p <= BAND[1] for p in ps),
        "too_hard": mean(p < TOO_HARD for p in ps),
        "too_easy": mean(p > TOO_EASY for p in ps),
        "accuracy": correct / TRIALS,
        "frustrations": frustrations,
    }


def simulate(n: int, seed: int) -> dict[str, dict[str, dict[str, float]]]:
    out: dict[str, dict[str, dict[str, float]]] = {}
    for sc in SCENARIOS:
        out[sc.name] = {}
        for policy in POLICIES:
            rng = random.Random(seed)  # same learners and same luck for every policy
            thetas = [rng.gauss(0, 1.5) for _ in range(n)]
            runs = [run_learner(th, policy, sc, rng) for th in thetas]
            out[sc.name][policy] = {k: mean(r[k] for r in runs) for k in runs[0]}
    return out


def render(results: dict, n: int, seed: int) -> str:
    lines = [
        "# Personalization simulation: results",
        "",
        f"Generated by `uv run python -m app.scripts.simulate_learners --write` "
        f"({n} synthetic learners per cell, ability ~ N(0, 1.5), {TRIALS} exercises each, "
        f"seed {seed}). Method and limits: [personalization.md](../personalization.md).",
        "",
        f"**Productive band** = the learner's true chance of success is "
        f"{BAND[0]:.0%}-{BAND[1]:.0%}. *Too hard* < {TOO_HARD:.0%}, *too easy* > "
        f"{TOO_EASY:.0%}. *Error runs* = times a learner got {FRUSTRATION_STREAK} wrong in a "
        "row (per 300 exercises).",
    ]
    for sc, by_policy in results.items():
        lines += [
            "",
            f"## {sc}",
            "",
            "| Policy | In productive band | Too hard | Too easy | Accuracy | Error runs |",
            "|---|---|---|---|---|---|",
        ]
        for policy, m in by_policy.items():
            lines.append(
                f"| {policy} | {m['in_band']:.0%} | {m['too_hard']:.0%} | {m['too_easy']:.0%} "
                f"| {m['accuracy']:.0%} | {m['frustrations']:.1f} |"
            )
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    args = sys.argv[1:]
    n = int(args[args.index("--learners") + 1]) if "--learners" in args else 300
    seed = int(args[args.index("--seed") + 1]) if "--seed" in args else 7
    report = render(simulate(n, seed), n, seed)
    print(report)
    if "--write" in args:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
