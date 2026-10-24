"""Phase 0 scoring validation: score the labelled benchmark and write a report.

    uv run python -m app.scripts.validate_scoring            # print the report
    uv run python -m app.scripts.validate_scoring --write    # also update docs/validation

Gold labels in app/validation/benchmarks/naming_errors.csv were written by the project team
(author-labelled, synthetic). They test the code against the PNT decision tree; they are
not a substitute for labels from speech and language therapists (Phase 1, see
docs/validation/protocols/phase1-slp-panel.md).
"""

import csv
import json
import sys
from pathlib import Path

from app.analysis.errors import ERROR_TYPES, classify_naming
from app.analysis.scoring import score_naming
from app.exercises.catalog import load_catalog
from app.validation import metrics

BENCHMARKS = Path(__file__).parents[1] / "validation" / "benchmarks"
# Development set: the classifier was tuned while looking at it. Held-out set: written after
# tuning finished and scored once; its numbers are the honest estimate.
SETS = {
    "development": BENCHMARKS / "naming_errors.csv",
    "held-out": BENCHMARKS / "naming_errors_heldout.csv",
}
REPORT = Path(__file__).parents[3] / "docs" / "validation" / "results" / "scoring.md"


class _Answers(dict):
    """Accepted answers per word; a benchmark word not (or no longer) in the picture library
    is accepted only as itself."""

    def __missing__(self, word: str) -> list[str]:
        return [word]


def accepted_answers() -> dict[str, list[str]]:
    catalog = load_catalog()
    out: dict[str, list[str]] = _Answers()
    for e in catalog["stimuli"] + catalog.get("photos", []):
        if "picture_naming" in e.get("exercise_types", ["picture_naming"]):
            out.setdefault(e["target"], [])
            out[e["target"]] = sorted(set(out[e["target"]]) | set(e["accepted_answers"]))
    return out


def run(path: Path) -> dict:
    answers = accepted_answers()
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    gold, pred, gold_ok, app_ok, misses = [], [], [], [], []
    for r in rows:
        accepted = answers[r["target"]]
        result = score_naming(r["response"], r["target"], accepted)
        predicted = classify_naming(r["response"], r["target"], accepted, result.outcome)
        gold.append(r["expected_type"])
        pred.append(predicted)
        gold_ok.append(r["expected_type"] == "correct")
        app_ok.append(result.outcome == "correct")
        if predicted != r["expected_type"] or gold_ok[-1] != app_ok[-1]:
            misses.append(
                (r["target"], r["response"], r["expected_type"], predicted, result.outcome)
            )
    return {
        "n": len(rows),
        "agreement": metrics.percent_agreement(gold, pred),
        "kappa": metrics.cohen_kappa(gold, pred),
        "ac1": metrics.gwet_ac1(gold, pred),
        "per_class": metrics.per_class(gold, pred),
        "confusion": metrics.confusion(gold, pred),
        "correctness": metrics.accept_rates(gold_ok, app_ok),
        "correctness_kappa": metrics.cohen_kappa(
            [str(x) for x in gold_ok], [str(x) for x in app_ok]
        ),
        "misses": misses,
    }


def render(name: str, path: Path, r: dict) -> str:
    c = r["correctness"]
    lines = [
        f"## {name.capitalize()} set",
        "",
        f"`{path.relative_to(path.parents[3]).as_posix()}`: {r['n']} author-labelled responses.",
        "",
        "### Correct / not correct (the decision the patient sees)",
        "",
        "| Measure | Value | Target |",
        "|---|---|---|",
        f"| False-accept rate (wrong answer scored correct) | {c['false_accept_rate']:.1%} "
        f"of {c['n_wrong']} | ≤ 5% |",
        f"| False-reject rate (right answer not accepted) | {c['false_reject_rate']:.1%} "
        f"of {c['n_right']} | ≤ 10% |",
        f"| Cohen's kappa | {r['correctness_kappa']:.2f} | ≥ 0.80 |",
        "",
        "### Error type (information for the clinician)",
        "",
        f"Agreement {r['agreement']:.1%} · Cohen's kappa {r['kappa']:.2f} · "
        f"Gwet's AC1 {r['ac1']:.2f} (target kappa ≥ 0.74, ParAlg-level F1 ≈ 0.87)",
        "",
        "| Error type | n | Precision | Recall | F1 |",
        "|---|---|---|---|---|",
    ]
    for k in ERROR_TYPES:
        if k in r["per_class"]:
            m = r["per_class"][k]
            lines.append(
                f"| {k} | {m['n']} | {m['precision']:.2f} | {m['recall']:.2f} | {m['f1']:.2f} |"
            )
    cols = [k for k in ERROR_TYPES if k in r["confusion"]]
    lines += [
        "",
        "Confusion matrix (rows = gold label, columns = app):",
        "",
        "| gold \\ app | " + " | ".join(cols) + " |",
        "|---|" + "---|" * len(cols),
    ]
    for g in cols:
        lines.append(f"| {g} | " + " | ".join(str(r["confusion"][g][p] or "") for p in cols) + " |")
    lines += [
        "",
        "### Every disagreement",
        "",
        "| Target | Response | Gold | App type | App outcome |",
        "|---|---|---|---|---|",
    ]
    lines += [
        f"| {t} | {resp or '(empty)'} | {g} | {p} | {o} |" for t, resp, g, p, o in r["misses"]
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    results = {name: run(path) for name, path in SETS.items()}
    report = "\n".join(
        [
            "# Scoring validation: results",
            "",
            "Generated by `uv run python -m app.scripts.validate_scoring --write`. "
            "Do not edit by hand. Gold labels are author-written and synthetic: see "
            "[scoring.md](../scoring.md) for what this does and does not show.",
            "",
        ]
        + [render(name, SETS[name], r) for name, r in results.items()]
    )
    if "--json" in sys.argv:
        print(
            json.dumps(
                {n: {k: v for k, v in r.items() if k != "confusion"} for n, r in results.items()},
                default=str,
            )
        )
    else:
        print(report)
    if "--write" in sys.argv:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(report, encoding="utf-8")


if __name__ == "__main__":
    main()
