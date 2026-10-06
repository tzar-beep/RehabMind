"""Run the three GenAI prompt scenarios against the configured local LLM and print each
prompt, the raw model output and the validation verdict. No database needed.

Usage (Ollama running, model pulled):
  uv run python -m app.scripts.genai_demo            # uses OLLAMA_MODEL from .env
  uv run python -m app.scripts.genai_demo --json out.json
"""

import argparse
import asyncio
import json
import time

from app.ai import feedback, personalization, summary
from app.ai.ollama import OllamaAIProvider
from app.clinical.models import ConstraintSet
from app.core.config import get_settings
from app.exercises.models import Stimulus
from app.validation.exercise import check_clinical, check_safety, check_schema
from app.validation.generated_text import check_feedback, check_summary

DOG = Stimulus(
    slug="photo_scene_dog_running",
    target="The dog is running.",
    accepted_answers=["the dog is running", "a dog is running"],
    category="animals",
    difficulty=2,
    exercise_types=["picture_description", "sentence_construction"],
    is_active=True,
    task={
        "description": {
            "concepts": [
                {"name": "dog", "terms": ["dog", "puppy"], "optional": False},
                {"name": "running", "terms": ["running", "runs", "run"], "optional": False},
            ]
        },
        "sentence": {"words": ["the", "dog", "is", "running"]},
    },
)
CUP = Stimulus(
    slug="photo_cup_01",
    target="cup",
    accepted_answers=["cup", "mug"],
    category="household",
    difficulty=1,
    exercise_types=["picture_naming"],
    is_active=True,
    task={},
)
CS = ConstraintSet(
    min_difficulty=1,
    max_difficulty=3,
    allowed_categories=None,
    allowed_exercise_types=["picture_naming", "sentence_construction", "picture_description"],
    allowed_response_modes=["text", "speech"],
)


def exercise_input(kind: str, stim: Stimulus, objective: str, label: str, skill: str) -> dict:
    return {
        "objective": objective,
        "objective_label": label,
        "target_skill": skill,
        "exercise_type": kind,
        "target_difficulty": stim.difficulty,
        "min_difficulty": 1,
        "max_difficulty": 3,
        "allowed_categories": [],
        "recent_outcomes": ["correct", "incorrect", "near_miss", "incorrect"],
        "recent_answers": 8,
        "recent_accuracy": 0.62,
        "trend": "steady",
        "status": "progressing",
        "ability": 0.21,
        "predicted_success": 0.66,
        "weakness": "lower accuracy in category food",
        "category_accuracy": {"food": 0.4, stim.category: 0.7},
        "category_counts": {"food": 5, stim.category: 3},
        "candidates": [
            {
                "slug": stim.slug,
                **({} if kind == "picture_description" else {"target": stim.target}),
                "category": stim.category,
                "difficulty": stim.difficulty,
                "kind": "photo",
                "seen": False,
            }
        ],
    }


SCENARIOS = [
    (
        "1a exercise: picture naming (word retrieval)",
        "exercise",
        exercise_input(
            "picture_naming",
            CUP,
            "word_retrieval",
            "Improve word retrieval",
            "finding and saying the name of an everyday object",
        ),
        CUP,
    ),
    (
        "1b exercise: sentence construction (sentence formation)",
        "exercise",
        exercise_input(
            "sentence_construction",
            DOG,
            "sentence_formation",
            "Improve sentence formation",
            "putting words in the right order to make a simple sentence",
        ),
        DOG,
    ),
    (
        "1c exercise: picture description (descriptive language)",
        "exercise",
        exercise_input(
            "picture_description",
            DOG,
            "descriptive_language",
            "Improve descriptive language",
            "describing who is in a picture, what is happening and where",
        ),
        DOG,
    ),
    (
        "2 feedback: picture description, partly described",
        "feedback",
        {
            "objective": "descriptive_language",
            "objective_label": "Improve descriptive language",
            "target_skill": "describing who is in a picture, what is happening and where",
            "exercise_type": "picture_description",
            "difficulty": 2,
            "target": "A man is riding a bicycle.",
            "response": "someone is riding",
            "mode": "speech",
            "outcome": "near_miss",
            "score": 0.67,
            "hints_used": 0,
            "analysis": "key ideas mentioned: man, riding; key ideas not mentioned: bicycle",
        },
        None,
    ),
    (
        "3 summary: three objectives",
        "summary",
        {
            "period": "all recorded practice",
            "sessions_completed": 4,
            "objectives": [
                {
                    "objective": "word_retrieval",
                    "label": "Word retrieval",
                    "exercise": "picture naming",
                    "answers": 20,
                    "percent_correct": 65,
                    "trend": "improving",
                },
                {
                    "objective": "sentence_formation",
                    "label": "Sentence formation",
                    "exercise": "sentence construction",
                    "answers": 8,
                    "percent_correct": 50,
                    "trend": "steady",
                },
                {
                    "objective": "descriptive_language",
                    "label": "Descriptive language",
                    "exercise": "picture description",
                    "answers": 6,
                    "percent_correct": 33,
                    "trend": "not enough data",
                },
            ],
        },
        None,
    ),
]


async def run() -> list[dict]:
    s = get_settings()
    provider = OllamaAIProvider(s.ollama_base_url, s.ollama_model, timeout_s=120)
    results = []
    for title, kind, inp, stim in SCENARIOS:
        if kind == "exercise":
            req = personalization.build_request(inp)
        elif kind == "feedback":
            req = feedback.build_request(inp)
        else:
            req = summary.build_request(inp)
        started = time.perf_counter()
        res = await provider.generate(req)
        ms = int((time.perf_counter() - started) * 1000)
        if kind == "exercise":
            v = check_schema(res.raw_output)
            if v.ok and v.output:
                v = check_clinical(v.output, CS, {stim.slug: stim}, inp["exercise_type"])
                if v.ok and v.output:
                    v = check_safety(v.output, stim, inp["exercise_type"])
        elif kind == "feedback":
            v, _ = check_feedback(res.raw_output, inp["outcome"])
        else:
            v, _ = check_summary(res.raw_output, inp)
        verdict = "valid" if v.ok else f"rejected at {v.stage}: {', '.join(v.reasons)}"
        print(f"\n=== {title} ({req.prompt_version}) ===")
        print(f"model {res.model} · {ms} ms · tokens {res.usage}")
        print("--- user prompt ---\n" + req.user_prompt)
        print("--- raw output ---\n" + res.raw_output)
        print("--- validation --- " + verdict)
        results.append(
            {
                "title": title,
                "prompt_version": req.prompt_version,
                "model": res.model,
                "latency_ms": ms,
                "usage": res.usage,
                "user_prompt": req.user_prompt,
                "raw_output": res.raw_output,
                "validation": verdict,
            }
        )
    return results


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--json", help="also write results to this file")
    out_path = p.parse_args().json
    results = asyncio.run(run())
    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)


if __name__ == "__main__":
    main()
