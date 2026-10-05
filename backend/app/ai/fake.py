"""Deterministic, offline AI provider for development, demos and tests ($0, no network).

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
    "provider_error",
)

_PROMPTS = ("What is this?", "What do you call this?", "Can you name this?", "What is this called?")


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

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        self.calls += 1
        inp = request.input
        seed = _seed(request.prompt_version, inp, self.calls)
        fault = self._fault(seed)
        if fault == "provider_error":
            raise AIProviderError("simulated provider timeout")

        stim, why = self._choose(inp, seed)
        target: str = stim["target"]
        out: dict[str, Any] = {
            "stimulus_slug": stim["slug"],
            "difficulty": stim["difficulty"],
            "prompt": _PROMPTS[seed % len(_PROMPTS)],
            "semantic_cue": SEMANTIC_CUES.get(stim["category"], DEFAULT_SEMANTIC_CUE),
            "phonemic_cue": phonemic_prefix(target),
            "rationale": why.value,
        }
        if fault == "out_of_range_difficulty":
            out["difficulty"] = (
                min(5, inp["max_difficulty"] + 1) if inp["max_difficulty"] < 5 else 0
            )
        elif fault == "unknown_stimulus":
            out["stimulus_slug"] = "stethoscope"
        elif fault == "unsafe_text":
            out["semantic_cue"] = "Naming this will help your brain heal faster."
        elif fault == "answer_leak":
            out["prompt"] = f"Is this a {target}?"
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
