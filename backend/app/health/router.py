import asyncio
import logging

import boto3
from botocore.config import Config
from fastapi import APIRouter, Response, status
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import engine
from app.core.redis import redis_client

router = APIRouter(prefix="/health", tags=["health"])
log = logging.getLogger(__name__)


@router.get("/live")
async def live() -> dict[str, str]:
    return {"status": "ok"}


def _check_storage() -> None:
    s = get_settings()
    client = boto3.client(
        "s3",
        endpoint_url=s.s3_endpoint_url,
        region_name=s.s3_region,
        aws_access_key_id=s.minio_root_user,
        aws_secret_access_key=s.minio_root_password.get_secret_value()
        if s.minio_root_password
        else None,
        config=Config(connect_timeout=2, read_timeout=2, retries={"max_attempts": 1}),
    )
    client.head_bucket(Bucket=s.s3_bucket_audio)


@router.get("/ready")
async def ready(response: Response) -> dict[str, str]:
    """Reports dependency reachability only; never includes error details."""

    async def db() -> None:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))

    checks = {
        "database": db(),
        "redis": redis_client.ping(),
        "storage": asyncio.to_thread(_check_storage),
    }
    result: dict[str, str] = {}
    for name, coro in checks.items():
        try:
            await asyncio.wait_for(coro, timeout=3)
            result[name] = "ok"
        except Exception:
            log.warning("readiness check failed", extra={"data": {"check": name}})
            result[name] = "unavailable"
    if any(v != "ok" for v in result.values()):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return result
