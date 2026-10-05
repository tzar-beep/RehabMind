"""Server-side sessions in Redis.

The browser holds only an opaque random token (HttpOnly cookie). Redis stores the session
under the token's SHA-256 so a Redis read does not yield usable cookies.
Sessions expire on idle timeout and on an absolute lifetime, and can be revoked
individually or for all of a user's devices.
"""

import hashlib
import json
import secrets
import time
import uuid
from dataclasses import asdict, dataclass

from redis.asyncio import Redis

from app.core.config import Settings


def now() -> float:
    return time.time()


@dataclass
class SessionData:
    user_id: str
    role: str
    created_at: float
    last_seen: float


def _key(token: str) -> str:
    return "sess:" + hashlib.sha256(token.encode()).hexdigest()


def _index(user_id: str) -> str:
    return f"user_sessions:{user_id}"


class SessionStore:
    def __init__(self, redis: Redis, settings: Settings) -> None:
        self.redis = redis
        self.idle = settings.session_idle_timeout_seconds
        self.absolute = settings.session_absolute_timeout_seconds

    async def create(self, user_id: uuid.UUID, role: str) -> str:
        token = secrets.token_urlsafe(32)
        t = now()
        data = SessionData(str(user_id), role, t, t)
        async with self.redis.pipeline(transaction=True) as p:
            p.set(_key(token), json.dumps(asdict(data)), ex=self.idle)
            p.sadd(_index(data.user_id), _key(token))
            p.expire(_index(data.user_id), self.absolute)
            await p.execute()
        return token

    async def get(self, token: str) -> SessionData | None:
        raw = await self.redis.get(_key(token))
        if raw is None:
            return None
        data = SessionData(**json.loads(raw))
        t = now()
        if t - data.created_at >= self.absolute or t - data.last_seen >= self.idle:
            await self.revoke(token)
            return None
        data.last_seen = t
        ttl = int(min(self.idle, self.absolute - (t - data.created_at))) or 1
        await self.redis.set(_key(token), json.dumps(asdict(data)), ex=ttl)
        return data

    async def revoke(self, token: str) -> None:
        raw = await self.redis.get(_key(token))
        await self.redis.delete(_key(token))
        if raw:
            await self.redis.srem(_index(json.loads(raw)["user_id"]), _key(token))

    async def revoke_all(self, user_id: uuid.UUID) -> None:
        keys = await self.redis.smembers(_index(str(user_id)))
        if keys:
            await self.redis.delete(*keys)
        await self.redis.delete(_index(str(user_id)))
