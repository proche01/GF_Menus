"""FastAPI dependency injection helpers."""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
import redis.asyncio as aioredis

from app.config import Settings, get_settings
from app.database import get_db


async def get_redis(settings: Settings = Depends(get_settings)) -> aioredis.Redis:
    """Yield an async Redis client."""
    client = aioredis.from_url(settings.redis_url, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


def get_settings_dep() -> Settings:
    return get_settings()
