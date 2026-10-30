"""Phase 0 GenAI audit: what the local LLM produces, and what the validators stop.

    uv run python -m app.scripts.genai_audit [--repeats 4] [--feedback 120] [--write]

Runs the production prompts against the configured Ollama model for every catalogue
picture and exercise type (`--repeats` times each), and for feedback on benchmark answers.
Every raw output is put through the production validators, with the same two-attempt retry
the app uses. No database and no patient data are involved.

Writes (with --write):
  docs/validation/results/genai-audit.md           summary tables
  docs/validation/results/genai-audit.jsonl        every generation, for re-analysis
  docs/validation/review-packets/phase1-items.csv  blinded items for the clinician panel
  docs/validation/review-packets/phase1-key.csv    which items are AI / rule-based (keep
                                                   away from raters until rating is done)
"""

import argparse
import asyncio
import csv
import json
import random
import re
import sys
import time
from collections import Counter, defaultdict
from pathlib import Path
from statistics import mean, median

from app.ai import feedback, personalization
from app.ai.ollama import OllamaAIProvider
from app.ai.prompts import describe_analysis
from app.analysis.scoring import score_naming
from app.clinical.models import ConstraintSet
from app.core.config import get_settings
from app.exercises.catalog import load_catalog
from app.exercises.cues import rule_cues
from app.exercises.generator import DEFAULT_PROMPTS
from app.exercises.models import Stimulus
from app.exercises.types import OBJECTIVE_LABELS, OBJECTIVES, TARGET_SKILLS
from app.scripts.validate_scoring import SETS, accepted_answers
from app.validation import plain_language
from app.validation.exercise import check_clinical, check_safety, check_schema
from app.validation.generated_text import check_feedback

ROOT = Path(__file__).parents[3] / "docs" / "validation"
ATTEMPTS = 2  # same bounded retry as app.ai.runner.MAX_ATTEMPTS
CANDIDATES = 3
PACKET_PER_SOURCE = 24
TYPES = ["picture_naming", "sentence_construction", "picture_description"]


def stimuli() -> list[Stimulus]:
    catalog = load_catalog()
    out = [
        Stimulus(
            slug=e["slug"],
            target=e["target"],
            accepted_answers=e["accepted_answers"],
            category=e["category"],
            difficulty=e["difficulty"],
            exercise_types=["picture_naming"],
            kind="icon",
            task={},
            is_active=True,
        )
        for e in catalog["stimuli"]
    ]
    out += [
        Stimulus(
            slug=p["slug"],
            target=p["target"],
            accepted_answers=p["accepted_answers"],
            category=p["category"],
            difficulty=p["difficulty"],
            exercise_types=p["exercise_types"],
            kind="photo",
            task={k: p[k] for k in ("description", "sentence") if k in p},
            is_active=True,
        )
        for p in catalog.get("photos", [])
    ]
    return out


CS = ConstraintSet(
    min_difficulty=1,
    max_difficulty=5,
    allowed_categories=None,
    allowed_exercise_types=TYPES,
    allowed_response_modes=["text", "speech"],
)


def exercise_input(kind: str, stim: Stimulus, pool: list[Stimulus]) -> dict:
    objective = OBJECTIVES[kind]
    return {
        "objective": objective.value,
        "objective_label": OBJECTIVE_LABELS[objective],
        "target_skill": TARGET_SKILLS[objective],
        "exercise_type": kind,
        "target_difficulty": stim.difficulty,
        "min_difficulty": 1,
        "max_difficulty": 5,
        "allowed_categories": [],
        "recent_outcomes": ["correct", "incorrect", "near_miss"],
        "recent_answers": 6,
        "recent_accuracy": 0.6,
        "trend": "steady",
        "status": "progressing",
        "ability": 0.0,
        "predicted_success": 0.6,
        "weakness": "none identified",
        "category_accuracy": {},
        "category_counts": {},
        "candidates": [
            {
                "slug": s.slug,
                **({} if kind == "picture_description" else {"target": s.target}),
                "category": s.category,
                "difficulty": s.difficulty,
                "kind": s.kind,
                "seen": False,
                **personalization.prompt_facts(s, kind),
            }
            for s in pool
        ],
    }


def validate_exercise(raw: str, kind: str, pool: dict[str, Stimulus]):
    v = check_schema(raw)
    if v.ok and v.output:
        v = check_clinical(v.output, CS, pool, kind)
        if v.ok and v.output:
            v = check_safety(v.output, pool[v.output.stimulus_slug], kind)
    return v


def patient_texts(task: str, parsed: dict | None) -> list[str]:
    if not parsed:
        return []
    keys = ["prompt", "semantic_cue", "hint"] if task == "exercise" else ["feedback"]
    keys.append("optional_hint")
    return [parsed[k] for k in keys if parsed.get(k)]


async def generate(provider, req, validate) -> list[dict]:
    """Up to ATTEMPTS calls; one record per attempt."""
    records = []
    for attempt in range(1, ATTEMPTS + 1):
        started = time.perf_counter()
        try:
            res = await provider.generate(req)
            raw = res.raw_output
        except Exception as e:  # provider errors are part of what is audited
            raw, err = None, type(e).__name__
        ms = int((time.perf_counter() - started) * 1000)
        if raw is None:
            records.append({"attempt": attempt, "status": "error", "reasons": [err], "ms": ms})
            continue
        v = validate(raw)
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            parsed = None
        records.append(
            {
                "attempt": attempt,
                "status": "accepted" if v.ok else "rejected",
                "stage": v.stage,
                "reasons": v.reasons,
                "ms": ms,
                "raw": raw[:2000],
                "parsed": parsed if isinstance(parsed, dict) else None,
            }
        )
        if v.ok:
            break
    return records


async def run(repeats: int, n_feedback: int, seed: int) -> list[dict]:
    s = get_settings()
    provider = OllamaAIProvider(s.ollama_base_url, s.ollama_model, timeout_s=120)
    rng = random.Random(seed)
    all_stims = stimuli()
    jobs = []
    for kind in TYPES:
        eligible = [x for x in all_stims if kind in x.exercise_types]
        for stim in eligible:
            same = [x for x in eligible if x.difficulty == stim.difficulty and x is not stim]
            pool = [stim, *rng.sample(same, min(CANDIDATES - 1, len(same)))]
            for r in range(repeats):
                jobs.append(("exercise", kind, stim, pool, r))
    answers = accepted_answers()
    rows = list(csv.DictReader(SETS["development"].open(encoding="utf-8")))
    for row in rng.sample(rows, min(n_feedback, len(rows))):
        jobs.append(("feedback", "picture_naming", row, None, 0))

    out = []
    for i, (task, kind, item, pool, r) in enumerate(jobs, 1):
        if task == "exercise":
            pool_map = {x.slug: x for x in pool}
            req = personalization.build_request(exercise_input(kind, item, pool))
            records = await generate(
                provider, req, lambda raw, k=kind, p=pool_map: validate_exercise(raw, k, p)
            )
            meta = {"slug": item.slug, "target": item.target, "repeat": r}
        else:
            target = item["target"]
            result = score_naming(item["response"], target, answers[target])
            analysis = {"match_type": result.match_type, "similarity": result.similarity}
            inp = {
                "objective": "word_retrieval",
                "objective_label": OBJECTIVE_LABELS[OBJECTIVES[kind]],
                "target_skill": TARGET_SKILLS[OBJECTIVES[kind]],
                "exercise_type": kind,
                "difficulty": 2,
                "target": target,
                "response": item["response"] or "(no answer)",
                "mode": "text",
                "outcome": result.outcome,
                "score": result.score,
                "hints_used": 0,
                "analysis": describe_analysis(kind, analysis),
            }
            words = {w for t in [target, item["response"], *answers[target]] for w in t.split()}
            records = await generate(
                provider,
                feedback.build_request(inp),
                lambda raw, o=result.outcome, w=words: check_feedback(raw, o, w)[0],
            )
            meta = {"target": target, "response": item["response"], "outcome": result.outcome}
        out.append({"task": task, "exercise_type": kind, **meta, "attempts": records})
        if i % 25 == 0:
            print(f"{i}/{len(jobs)}", file=sys.stderr, flush=True)
    return out


def summarise(results: list[dict]) -> str:
    lines = [
        "# GenAI audit: results",
        "",
        "Generated by `uv run python -m app.scripts.genai_audit --write`. "
        "Method and limits: [genai.md](../genai.md). Raw records: `genai-audit.jsonl`.",
        "",
    ]
    model = get_settings().ollama_model
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        groups[f"{r['task']} · {r['exercise_type']}"].append(r)
    lines += [
        f"Model `{model}`, prompts `{personalization.PROMPT_VERSION}` / "
        f"`{feedback.FEEDBACK_PROMPT_VERSION}`, temperature as in production.",
        "",
        "## Outcome per request (two attempts, as in the app)",
        "",
        "| Task | Requests | Valid first time | Valid after retry | Fallback used | "
        "Median latency |",
        "|---|---|---|---|---|---|",
    ]
    for name, rs in sorted(groups.items()):
        first = mean(r["attempts"][0]["status"] == "accepted" for r in rs)
        any_ok = mean(any(a["status"] == "accepted" for a in r["attempts"]) for r in rs)
        ms = median(a["ms"] for r in rs for a in r["attempts"])
        lines.append(
            f"| {name} | {len(rs)} | {first:.0%} | {any_ok:.0%} | {1 - any_ok:.0%} | "
            f"{ms / 1000:.1f} s |"
        )

    attempts = [(r, a) for r in results for a in r["attempts"]]
    raw_n = len(attempts)
    codes: Counter = Counter()
    for _, a in attempts:
        codes.update({re.sub(r":.*", "", c) for c in a.get("reasons", [])})
    lines += [
        "",
        f"## What the validators caught ({raw_n} raw generations)",
        "",
        "Share of raw model outputs with each problem. None of these reach a patient: a "
        "rejected output is retried once, then replaced by the rule-based version.",
        "",
        "| Reason code | Outputs | Share |",
        "|---|---|---|",
    ]
    for code, n in codes.most_common():
        lines.append(f"| `{code}` | {n} | {n / raw_n:.1%} |")

    accepted = [(r, a) for r, a in attempts if a["status"] == "accepted"]
    texts = [t for r, a in accepted for t in patient_texts(r["task"], a.get("parsed"))]
    words = [w for t in texts for w in re.findall(r"[a-z']+", t.lower())]
    sentences = [s for t in texts for s in re.split(r"[.!?]+", t) if s.strip()]
    everyday = mean(plain_language._zipf(w) >= 4.0 for w in words) if words else 0
    distinct: dict[tuple, set] = defaultdict(set)
    for r, a in accepted:
        if r["task"] == "exercise" and a.get("parsed"):
            distinct[(r["exercise_type"], r["slug"])].add(a["parsed"].get("prompt"))
    lines += [
        "",
        "## Language of accepted (patient-facing) text",
        "",
        "| Measure | Value |",
        "|---|---|",
        f"| Texts | {len(texts)} |",
        f"| Mean words per sentence | {mean(len(s.split()) for s in sentences):.1f} |"
        if sentences
        else "| Mean words per sentence | n/a |",
        f"| Words that are everyday English (Zipf ≥ 4) | {everyday:.0%} |",
        f"| Distinct prompts per picture across repeats (mean) | "
        f"{mean(len(v) for v in distinct.values()):.1f} |"
        if distinct
        else "| Distinct prompts per picture | n/a |",
    ]
    return "\n".join(lines) + "\n"


def review_packet(results: list[dict], seed: int) -> tuple[list[dict], list[dict]]:
    """Blinded items: accepted AI naming cues vs the rule-based cues for the same pictures."""
    rng = random.Random(seed)
    ai = [
        (r, a["parsed"])
        for r in results
        if r["task"] == "exercise" and r["exercise_type"] == "picture_naming"
        for a in r["attempts"]
        if a["status"] == "accepted" and a.get("parsed")
    ]
    seen, picked = set(), []
    for _r, p in rng.sample(ai, len(ai)):
        if p["stimulus_slug"] not in seen and len(picked) < PACKET_PER_SOURCE:
            seen.add(p["stimulus_slug"])
            picked.append((p["stimulus_slug"], p["prompt"], p["semantic_cue"], p["phonemic_cue"]))
    by_slug = {s.slug: s for s in stimuli()}
    rule = []
    for slug, *_ in picked:
        stim = by_slug[slug]
        cue1, cue2 = rule_cues(stim.category, stim.target)
        rule.append((slug, DEFAULT_PROMPTS["picture_naming"], cue1, cue2))
    items = [("ai", *x) for x in picked] + [("rule", *x) for x in rule]
    rng.shuffle(items)
    sheet, key = [], []
    for n, (source, slug, prompt, cue1, cue2) in enumerate(items, 1):
        item_id = f"N{n:03d}"
        stim = by_slug[slug]
        sheet.append(
            {
                "item_id": item_id,
                "picture": stim.target,
                "image": stim.slug,
                "question": prompt,
                "meaning_cue": cue1,
                "sound_cue": cue2 if source == "rule" else f"It starts with “{cue2}…”",
            }
        )
        key.append({"item_id": item_id, "source": source, "slug": slug})
    return sheet, key


def main() -> None:
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--repeats", type=int, default=4)
    ap.add_argument("--feedback", type=int, default=120)
    ap.add_argument("--seed", type=int, default=11)
    ap.add_argument("--write", action="store_true")
    args = ap.parse_args()
    results = asyncio.run(run(args.repeats, args.feedback, args.seed))
    report = summarise(results)
    print(report)
    if args.write:
        out = ROOT / "results"
        out.mkdir(parents=True, exist_ok=True)
        (out / "genai-audit.md").write_text(report, encoding="utf-8")
        with (out / "genai-audit.jsonl").open("w", encoding="utf-8") as f:
            for r in results:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        sheet, key = review_packet(results, args.seed)
        packets = ROOT / "review-packets"
        packets.mkdir(parents=True, exist_ok=True)
        for name, rows in (("phase1-items.csv", sheet), ("phase1-key.csv", key)):
            if rows:
                with (packets / name).open("w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0]))
                    w.writeheader()
                    w.writerows(rows)


if __name__ == "__main__":
    main()
