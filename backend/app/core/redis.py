from redis.asyncio import Redis

from app.core.config import get_settings

_settings = get_settings()
redis_client: Redis = Redis.from_url(
    _settings.redis_url,
    password=_settings.redis_password.get_secret_value(),
    decode_responses=True,
)


def get_redis() -> Redis:
    return redis_client
