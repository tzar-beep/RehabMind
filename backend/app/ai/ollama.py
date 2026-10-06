"""Real generative AI: a local transformer LLM served by Ollama ($0, runs on this machine).

One HTTP call per request to Ollama's chat endpoint, with the task's JSON Schema passed as
`format` (Ollama's structured outputs: decoding is constrained to valid JSON of that shape).
The reply is still untrusted text: every caller validates it before use.

No tools, no conversation memory, no streaming. The frontend never talks to Ollama.
"""

from typing import Any

import httpx

from app.ai.provider import AIProviderError, GenerationRequest, GenerationResult

# Low temperature: varied but controlled wording; the schema and validators do the rest.
DEFAULT_OPTIONS: dict[str, Any] = {"temperature": 0.4, "top_p": 0.9, "num_predict": 400}
KEEP_ALIVE = "30m"  # keep the model loaded between exercises (first load takes seconds)


class OllamaAIProvider:
    name = "ollama"

    def __init__(
        self,
        base_url: str,
        model: str,
        *,
        timeout_s: float = 20,
        transport: httpx.AsyncBaseTransport | None = None,
    ):
        """`transport` is a test hook (httpx.MockTransport)."""
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.AsyncClient(
            base_url=self.base_url, timeout=timeout_s, transport=transport
        )

    def payload(self, request: GenerationRequest) -> dict[str, Any]:
        return {
            "model": self.model,
            "messages": [
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
            "format": request.output_schema,
            "stream": False,
            "options": DEFAULT_OPTIONS,
            "keep_alive": KEEP_ALIVE,
        }

    async def generate(self, request: GenerationRequest) -> GenerationResult:
        try:
            r = await self._client.post("/api/chat", json=self.payload(request))
        except httpx.HTTPError as e:
            raise AIProviderError(f"ollama unreachable: {type(e).__name__}") from e
        if r.status_code != 200:
            raise AIProviderError(f"ollama returned HTTP {r.status_code}")
        try:
            data = r.json()
            content = data["message"]["content"]
        except (ValueError, KeyError, TypeError) as e:
            raise AIProviderError("ollama reply missing message content") from e
        if not isinstance(content, str) or not content.strip():
            raise AIProviderError("ollama returned empty content")
        return GenerationResult(
            raw_output=content,
            provider=self.name,
            model=str(data.get("model") or self.model),
            usage={
                "prompt_tokens": int(data.get("prompt_eval_count") or 0),
                "output_tokens": int(data.get("eval_count") or 0),
                "total_ms": int((data.get("total_duration") or 0) / 1_000_000),
            },
        )

    async def status(self) -> dict[str, Any]:
        """Is the server up, and is the configured model downloaded?"""
        try:
            r = await self._client.get("/api/tags", timeout=3)
            names = {m.get("name") for m in r.json().get("models", [])}
        except (httpx.HTTPError, ValueError, AttributeError):
            return {"reachable": False, "model_available": False}
        return {"reachable": True, "model_available": self.model in names}
