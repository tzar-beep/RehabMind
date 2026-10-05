"""Clear login rate-limit counters. Development only (used before e2e runs).

Usage:  uv run python -m app.scripts.reset_rate_limits
"""

import asyncio
import sys

from app.core.config import get_settings
from app.core.redis import redis_client


async def _main() -> int:
    keys = [k async for k in redis_client.scan_iter("rl:login:*")]
    if keys:
        await redis_client.delete(*keys)
    return len(keys)


if __name__ == "__main__":
    if get_settings().app_env != "development":
        sys.exit("refused: APP_ENV is not 'development'")
    print(f"cleared {asyncio.run(_main())} rate-limit keys")
