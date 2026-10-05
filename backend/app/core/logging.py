import json
import logging
import sys
from contextvars import ContextVar
from datetime import UTC, datetime

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Keys whose values must never reach logs.
_REDACT = {"password", "password_hash", "token", "session", "cookie", "authorization", "audio"}


def _redact(value: object) -> object:
    if isinstance(value, dict):
        return {
            k: "[redacted]" if any(r in k.lower() for r in _REDACT) else _redact(v)
            for k, v in value.items()
        }
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, object] = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if rid := request_id_var.get():
            entry["request_id"] = rid
        if extra := getattr(record, "data", None):
            entry["data"] = _redact(extra)
        if record.exc_info:
            entry["exc"] = self.formatException(record.exc_info)
        return json.dumps(entry, default=str)


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers[:] = [handler]
    root.setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").disabled = True  # access lines carry cookies/paths
