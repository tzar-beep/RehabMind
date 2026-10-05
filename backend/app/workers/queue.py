import uuid
from typing import Protocol

from arq import ArqRedis, create_pool
from arq.connections import RedisSettings

from app.core.config import get_settings


def redis_settings() -> RedisSettings:
    s = get_settings()
    rs = RedisSettings.from_dsn(s.redis_url)
    rs.password = s.redis_password.get_secret_value()
    return rs


class JobQueue(Protocol):
    async def enqueue_speech(self, asset_id: uuid.UUID) -> None: ...


class ArqQueue:
    def __init__(self) -> None:
        self._pool: ArqRedis | None = None

    async def enqueue_speech(self, asset_id: uuid.UUID) -> None:
        if self._pool is None:
            self._pool = await create_pool(redis_settings())
        await self._pool.enqueue_job("process_speech", str(asset_id), _job_id=f"speech:{asset_id}")


_queue = ArqQueue()


def get_job_queue() -> JobQueue:
    return _queue
