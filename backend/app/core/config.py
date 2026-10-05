from functools import lru_cache
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    """Application settings. Required secrets have no defaults: startup fails if missing."""

    model_config = SettingsConfigDict(env_file=ROOT_ENV_FILE, extra="ignore")

    app_env: Literal["development", "test", "production"]

    postgres_host: str = "127.0.0.1"
    postgres_port: int = 5433
    postgres_db: str = "stroke_recovery"
    postgres_app_password: SecretStr
    postgres_migrator_password: SecretStr

    redis_url: str = "redis://127.0.0.1:6379/0"
    redis_password: SecretStr

    s3_endpoint_url: str | None = None
    s3_region: str = "us-east-1"
    s3_bucket_audio: str = "ephemeral-audio"
    minio_root_user: str | None = None
    minio_root_password: SecretStr | None = None

    seed_dev_password: SecretStr | None = None

    audio_encryption_key: SecretStr
    audio_max_bytes: int = 2_000_000
    whisper_model: str = "small.en"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"

    frontend_origins: list[str] = ["http://localhost:3000"]
    # Only trust X-Forwarded-For when a known proxy (the Next.js rewrite) fronts the API.
    trust_proxy_headers: bool = True

    session_idle_timeout_seconds: int = 30 * 60
    session_absolute_timeout_seconds: int = 12 * 60 * 60
    login_max_failures_per_account: int = 5
    login_max_attempts_per_ip: int = 30
    login_rate_window_seconds: int = 15 * 60

    @model_validator(mode="after")
    def _production_guards(self) -> "Settings":
        if self.app_env == "production":
            if any(o.startswith("http://") for o in self.frontend_origins):
                raise ValueError("production origins must be https")
            if "*" in self.frontend_origins:
                raise ValueError("wildcard origin is not allowed")
        return self

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def session_cookie_name(self) -> str:
        # __Host- prefix requires Secure; locally we run over http.
        return "__Host-sra_session" if self.is_production else "sra_session"

    def _db_url(self, user: str, password: SecretStr) -> str:
        pw = quote(password.get_secret_value(), safe="")
        return (
            f"postgresql+asyncpg://{user}:{pw}@{self.postgres_host}:"
            f"{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def database_url(self) -> str:
        return self._db_url("sra_app", self.postgres_app_password)

    @property
    def migration_database_url(self) -> str:
        return self._db_url("sra_migrator", self.postgres_migrator_password)


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
