"""Generative AI behind a provider interface.

One call = one bounded, structured request. No tools, no loops, no memory: the application
decides what to ask, validates what comes back, and decides whether to use it.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol

from app.core.config import get_settings


@dataclass(frozen=True)
class GenerationRequest:
    task: str  # e.g. "picture_naming.personalize"
    prompt_version: str
    system_prompt: str
    user_prompt: str
    # Minimal, pseudonymous structured input (also stored as the audit input snapshot).
    input: dict[str, Any]
    # JSON Schema the output must satisfy (for providers with structured-output support).
    output_schema: dict[str, Any]


@dataclass(frozen=True)
class GenerationResult:
    raw_output: str  # untrusted text; must pass validation before any use
    provider: str
    model: str
    model_version: str | None = None
    usage: dict[str, int] = field(default_factory=dict)


class AIProviderError(Exception):
    """Provider unavailable, timed out, or refused. Always recoverable via fallback."""


class AIProvider(Protocol):
    name: str

    async def generate(self, request: GenerationRequest) -> GenerationResult: ...


_provider: AIProvider | None = None


def get_ai_provider() -> AIProvider | None:
    """Configured provider, or None when AI personalization is disabled."""
    global _provider
    kind = get_settings().ai_provider
    if kind == "none":
        return None
    if _provider is None:
        settings = get_settings()
        if kind == "fake":
            from app.ai.fake import FakeAIProvider

            _provider = FakeAIProvider(fault_rate=settings.ai_fake_fault_rate)
        elif kind == "ollama":
            from app.ai.ollama import OllamaAIProvider

            _provider = OllamaAIProvider(
                settings.ollama_base_url, settings.ollama_model, timeout_s=settings.ai_timeout_s
            )
        else:  # pragma: no cover - guarded by settings validation
            raise ValueError(f"unknown AI provider {kind}")
    return _provider


def set_ai_provider(provider: AIProvider | None) -> None:
    """Test hook."""
    global _provider
    _provider = provider
