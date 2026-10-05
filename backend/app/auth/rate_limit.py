import hashlib

from redis.asyncio import Redis


def _h(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()[:32]


class LoginRateLimiter:
    """Fixed-window counters: failures per account, attempts per client IP."""

    def __init__(self, redis: Redis, *, max_failures: int, max_ip: int, window: int) -> None:
        self.redis, self.max_failures, self.max_ip, self.window = (
            redis,
            max_failures,
            max_ip,
            window,
        )

    async def _incr(self, key: str) -> int:
        async with self.redis.pipeline(transaction=True) as p:
            p.incr(key)
            p.expire(key, self.window, nx=True)
            count, _ = await p.execute()
        return int(count)

    async def allow_attempt(self, email: str, ip: str) -> bool:
        ip_count = await self._incr(f"rl:login:ip:{_h(ip)}")
        failures = int(await self.redis.get(f"rl:login:acct:{_h(email)}") or 0)
        return ip_count <= self.max_ip and failures < self.max_failures

    async def record_failure(self, email: str) -> None:
        await self._incr(f"rl:login:acct:{_h(email)}")

    async def reset(self, email: str) -> None:
        await self.redis.delete(f"rl:login:acct:{_h(email)}")
