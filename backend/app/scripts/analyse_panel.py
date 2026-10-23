"""Phase 1: prepare rating packets for the clinician panel and analyse the returned ratings.

    uv run python -m app.scripts.analyse_panel packets     # write blank scoring packet
    uv run python -m app.scripts.analyse_panel analyse     # analyse returned ratings

Protocol: docs/validation/protocols/phase1-slp-panel.md. Files, under docs/validation/:

  review-packets/phase1-items.csv        content items (from app.scripts.genai_audit)
  review-packets/phase1-key.csv          AI or rule-based, per content item (not for raters)
  review-packets/phase1-scoring.csv      responses to label (written by `packets`)
  review-packets/phase1-scoring-key.csv  the app's decisions (not for raters)
  panel/content/<rater>.csv              returned: item_id, relevance, clarity, tone,
                                         difficulty_fit (each 1-4), comment
  panel/scoring/<rater>.csv              returned: item_id, correct (yes/no), error_type
  results/panel.md                       written by `analyse`
"""

import csv
import random
import sys
from collections import defaultdict
from itertools import combinations
from pathlib import Path
from statistics import mean

from app.analysis.errors import ERROR_TYPES, classify_naming
from app.analysis.scoring import score_naming
from app.scripts.validate_scoring import SETS, accepted_answers
from app.validation import metrics

ROOT = Path(__file__).parents[3] / "docs" / "validation"
PACKETS = ROOT / "review-packets"
PANEL = ROOT / "panel"
DIMENSIONS = ["relevance", "clarity", "tone", "difficulty_fit"]
# Thresholds from Polit, Beck & Owen (2007) and the project protocol.
I_CVI_MIN = 0.78
S_CVI_AVE_MIN = 0.90
KAPPA_MIN = 0.74
FALSE_ACCEPT_MAX = 0.05
SCORING_PACKET_SIZE = 200  # about two hours of labelling per rater


def _read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _write(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)


def make_scoring_packet(seed: int = 5) -> int:
    answers = accepted_answers()
    rows = [r for path in SETS.values() for r in _read(path)]
    random.Random(seed).shuffle(rows)  # noqa: S311 - reproducible order, not security
    rows = rows[:SCORING_PACKET_SIZE]
    sheet, key = [], []
    for n, r in enumerate(rows, 1):
        item_id = f"S{n:03d}"
        result = score_naming(r["response"], r["target"], answers[r["target"]])
        sheet.append(
            {
                "item_id": item_id,
                "picture": r["target"],
                "response": r["response"],
                "correct": "",
                "error_type": "",
            }
        )
        key.append(
            {
                "item_id": item_id,
                "app_correct": "yes" if result.outcome == "correct" else "no",
                "app_error_type": classify_naming(
                    r["response"], r["target"], answers[r["target"]], result.outcome
                ),
                "author_label": r["expected_type"],
            }
        )
    _write(PACKETS / "phase1-scoring.csv", sheet)
    _write(PACKETS / "phase1-scoring-key.csv", key)
    for kind in ("content", "scoring"):
        (PANEL / kind).mkdir(parents=True, exist_ok=True)
    return len(sheet)


def analyse_content() -> list[str]:
    files = sorted((PANEL / "content").glob("*.csv"))
    key_path = PACKETS / "phase1-key.csv"
    if not files or not key_path.exists():
        return ["No content ratings returned yet (`panel/content/*.csv`)."]
    source = {r["item_id"]: r["source"] for r in _read(key_path)}
    ratings: dict[str, dict[str, list[int]]] = defaultdict(lambda: defaultdict(list))
    for f in files:
        for r in _read(f):
            for d in DIMENSIONS:
                if r.get(d, "").strip():
                    ratings[r["item_id"]][d].append(int(r[d]))
    lines = [
        f"{len(files)} rater(s), {len(ratings)} item(s) rated. Items count as relevant at 3 "
        f"or 4. Targets: I-CVI ≥ {I_CVI_MIN}, S-CVI/Ave ≥ {S_CVI_AVE_MIN}.",
        "",
        "| Source | Items | S-CVI/Ave | S-CVI/UA | Items below I-CVI | "
        + " | ".join(f"Mean {d.replace('_', ' ')}" for d in DIMENSIONS)
        + " |",
        "|---|---|---|---|---|" + "---|" * len(DIMENSIONS),
    ]
    for src in ("ai", "rule"):
        items = [i for i in ratings if source.get(i) == src and ratings[i]["relevance"]]
        if not items:
            continue
        cvi = metrics.content_validity([ratings[i]["relevance"] for i in items])
        low = sum(v < I_CVI_MIN for v in cvi["i_cvi"])
        means = [
            mean(x for i in items for x in ratings[i][d])
            if any(ratings[i][d] for i in items)
            else float("nan")
            for d in DIMENSIONS
        ]
        lines.append(
            f"| {'AI-written' if src == 'ai' else 'Rule-based'} | {len(items)} | "
            f"{cvi['s_cvi_ave']:.2f} | {cvi['s_cvi_ua']:.2f} | {low} | "
            + " | ".join(f"{m:.2f}" for m in means)
            + " |"
        )
    return lines


def analyse_scoring() -> list[str]:
    files = sorted((PANEL / "scoring").glob("*.csv"))
    key_path = PACKETS / "phase1-scoring-key.csv"
    if not files or not key_path.exists():
        return ["No scoring labels returned yet (`panel/scoring/*.csv`)."]
    key = {r["item_id"]: r for r in _read(key_path)}
    raters = {f.stem: {r["item_id"]: r for r in _read(f) if r.get("correct")} for f in files}
    lines = [
        f"{len(raters)} rater(s). Targets: kappa ≥ {KAPPA_MIN}, false-accept rate ≤ "
        f"{FALSE_ACCEPT_MAX:.0%}.",
        "",
        "| Comparison | Items | Correct/incorrect kappa | Error-type kappa | "
        "App false-accept rate |",
        "|---|---|---|---|---|",
    ]
    for a, b in combinations(raters, 2):
        common = sorted(set(raters[a]) & set(raters[b]))
        if common:
            ka = metrics.cohen_kappa(
                [raters[a][i]["correct"] for i in common], [raters[b][i]["correct"] for i in common]
            )
            ke = metrics.cohen_kappa(
                [raters[a][i]["error_type"] for i in common],
                [raters[b][i]["error_type"] for i in common],
            )
            lines.append(f"| {a} vs {b} | {len(common)} | {ka:.2f} | {ke:.2f} | — |")
    for name, labels in raters.items():
        common = sorted(i for i in labels if i in key)
        gold_ok = [labels[i]["correct"].strip().lower() == "yes" for i in common]
        app_ok = [key[i]["app_correct"] == "yes" for i in common]
        ka = metrics.cohen_kappa([str(x) for x in gold_ok], [str(x) for x in app_ok])
        typed = [i for i in common if labels[i]["error_type"] in ERROR_TYPES]
        ke = (
            metrics.cohen_kappa(
                [labels[i]["error_type"] for i in typed], [key[i]["app_error_type"] for i in typed]
            )
            if typed
            else float("nan")
        )
        fa = metrics.accept_rates(gold_ok, app_ok)["false_accept_rate"]
        lines.append(f"| App vs {name} | {len(common)} | {ka:.2f} | {ke:.2f} | {fa:.1%} |")
    return lines


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    command = sys.argv[1] if len(sys.argv) > 1 else "analyse"
    if command == "packets":
        print(f"wrote {make_scoring_packet()} scoring items to {PACKETS}")
        return
    report = "\n".join(
        [
            "# Clinician panel: results",
            "",
            "Generated by `uv run python -m app.scripts.analyse_panel analyse`. "
            "Protocol: [phase1-slp-panel.md](../protocols/phase1-slp-panel.md).",
            "",
            "## Content validity of exercise text",
            "",
            *analyse_content(),
            "",
            "## Scoring agreement",
            "",
            *analyse_scoring(),
        ]
    )
    print(report)
    (ROOT / "results").mkdir(parents=True, exist_ok=True)
    (ROOT / "results" / "panel.md").write_text(report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
