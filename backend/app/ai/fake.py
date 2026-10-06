"""Deterministic, offline stand-in for the LLM, for tests and offline development.

NOT generative AI: it fills templates. The real model is `OllamaAIProvider`; this provider
keeps tests fast and reproducible and lets the app run without Ollama.

Produces realistic personalization from the structured input, and — to demonstrate the
validation pipeline — deterministically injects a share of faulty outputs of the kinds real
models produce (malformed JSON, out-of-range difficulty, invented stimuli, unsafe wording,
answer leaks). Same input → same output.
"""

import hashlib
import json
from typing import Any

from app.ai.provider import AIProviderError, GenerationRequest, GenerationResult
from app.ai.schemas import Rationale
from app.exercises.cues import DEFAULT_SEMANTIC_CUE, SEMANTIC_CUES, phonemic_prefix

FAULTS = (
    "invalid_json",
    "out_of_range_difficulty",
    "unknown_stimulus",
    "unsafe_text",
    "answer_leak",
    "extra_field",
    "invented_image",
    "provider_error",
)

_PROMPTS = {
    "picture_naming": (
        "What is this?",
        "What do you call this?",
        "Can you name this?",
        "What is this called?",
    ),
    "picture_description": (
        "Describe what you see in the picture.",
        "What is happening in this picture?",
        "Tell me about this picture.",
    ),
    "sentence_construction": (
        "Build a sentence using these words.",
        "Put these words in order.",
        "Make a sentence from these words.",
    ),
}


_HINTS = {
    "picture_description": "Think about who you see and what is happening.",
    "sentence_construction": "Start with who is in the picture.",
}


def _seed(*parts: object) -> int:
    return int(hashlib.sha256(json.dumps(parts, sort_keys=True).encode()).hexdigest()[:12], 16)


class FakeAIProvider:
    name = "fake"
    model = "fake-personalizer"
    model_version = "1"

    def __init__(self, fault_rate: float = 0.0, fault_plan: list[str | None] | None = None):
        """`fault_plan` (tests): explicit fault per call, None = valid output."""
        self.fault_rate = fault_rate
        self.fault_plan = list(fault_plan) if fault_plan is not None else None
        self.calls = 0

    def _fault(self, seed: int) -> str | None:
        if self.fault_plan is not None:
            return self.fault_plan.pop(0) if self.fault_plan else None
        if (seed % 1000) / 1000 < self.fault_rate:
            return FAULTS[(seed // 1000) % len(FAULTS)]
        return None

    @staticmethod
    def _choose(inp: dict[str, Any], seed: int) -> tuple[dict[str, Any], Rationale]:
        candidates: list[dict[str, Any]] = inp["candidates"]
        recent: list[str] = inp["recent_outcomes"]
        acc: dict[str, float] = inp["category_accuracy"]
        weak = [c for c in candidates if acc.get(c["category"], 1.0) < 0.6]
        if recent[-2:] and all(o in ("incorrect", "skipped", "near_miss") for o in recent[-2:]):
            pool, why = weak or candidates, Rationale.REINFORCE_RECENT_ERROR
        elif len(recent) >= 3 and all(o == "correct" for o in recent[-3:]):
            unseen = [c for c in candidates if c.get("seen") is False]
            pool, why = unseen or candidates, Rationale.INTRODUCE_NEW
        elif weak:
            pool, why = weak, Rationale.CONSOLIDATE_SUCCESS
        else:
            least = min(
                {c["category"] for c in candidates},
                key=lambda cat: inp["category_counts"].get(cat, 0),
            )
            pool, why = (
                [c for c in candidates if c["category"] == least],
                Rationale.CATEGORY_VARIETY,
            )
        return pool[seed % len(pool)], why

    def _result(self, out: dict[str, Any]) -> GenerationResult:
        return GenerationResult(
            raw_output=json.dumps(out),
            provider=self.name,
            model=self.model,
            model_version=self.model_version,
        )

    def _feedback(self, inp: dict[str, Any]) -> GenerationResult:
        lead = {
            "correct": "Well done.",
            "near_miss": "You were very close.",
            "incorrect": "Good effort.",
            "skipped": "That is fine.",
        }[inp["outcome"]]
        tips = {
            "word_retrieval": "Say the first sound to yourself, then the whole word.",
            "sentence_formation": "Start with who is in the picture.",
            "descriptive_language": "Say who you see and what they are doing.",
        }
        return self._result(
            {
                "feedback": f"{lead} You worked on {inp['target_skill']}.",
                "optional_hint": tips[inp["objective"]],
            }
        )

    def _summary(self, inp: dict[str, Any]) -> GenerationResult:
        practised = [o for o in inp["objectives"] if o["answers"]]
        text = " ".join(
            f"{o['label']}: {o['percent_correct']}% correct over {o['answers']} answers."
            for o in practised
        )
        return self._result(
            {
                "summary": f"Practice {inp['period']}. {text}".strip(),
                "strengths": [f"Regular practice of {practised[0]['label'].lower()}."]
                if practised
                else [],
                "focus_areas": [],
            }
        )

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        self.calls += 1
        inp = request.input
        if request.task == "feedback.generate":
            return self._feedback(inp)
        if request.task == "progress.summarize":
            return self._summary(inp)
        seed = _seed(request.prompt_version, inp, self.calls)
        fault = self._fault(seed)
        if fault == "provider_error":
            raise AIProviderError("simulated provider timeout")

        stim, why = self._choose(inp, seed)
        target: str = stim.get("target", "")
        kind = inp.get("exercise_type", "picture_naming")
        prompts = _PROMPTS[kind]
        out: dict[str, Any] = {
            "stimulus_slug": stim["slug"],
            "difficulty": stim["difficulty"],
            "prompt": prompts[seed % len(prompts)],
            "rationale": why.value,
        }
        if kind == "picture_naming":
            out["semantic_cue"] = SEMANTIC_CUES.get(stim["category"], DEFAULT_SEMANTIC_CUE)
            out["phonemic_cue"] = phonemic_prefix(target)
        else:
            out["hint"] = _HINTS[kind]
        if fault == "out_of_range_difficulty":
            out["difficulty"] = (
                min(5, inp["max_difficulty"] + 1) if inp["max_difficulty"] < 5 else 0
            )
        elif fault == "unknown_stimulus":
            out["stimulus_slug"] = "stethoscope"
        elif fault == "unsafe_text":
            out["prompt"] = "This will help your brain heal."
        elif fault == "answer_leak":
            # Without the answer text (description), a model can still leak by guessing
            # from the picture's name, e.g. "photo_scene_dog_running" -> "dog running".
            guess = target or " ".join(stim["slug"].split("_")[2:])
            out["prompt"] = f"Is this a {guess}?" if kind == "picture_naming" else guess[:60]
        elif fault == "invented_image":
            out["image_url"] = "https://example.com/made-up-picture.jpg"
        elif fault == "extra_field":
            out["reasoning"] = "The patient struggles with food words, so..."

        raw = json.dumps(out)
        if fault == "invalid_json":
            raw = raw[: len(raw) // 2]
        return GenerationResult(
            raw_output=raw,
            provider=self.name,
            model=self.model,
            model_version=self.model_version,
            usage={"input_items": len(inp["candidates"])},
        )
