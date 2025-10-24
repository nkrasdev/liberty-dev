import os
from typing import Any, Optional

import redis.asyncio as redis
from shared.utils.logging import get_logger

logger = get_logger(__name__)

# Redis connection
redis_client: Optional[redis.Redis] = None


async def init_cache() -> None:
    """Initialize Redis cache connection."""
    global redis_client
    
    try:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        redis_client = redis.from_url(redis_url, decode_responses=True)
        
        # Test connection
        await redis_client.ping()
        logger.info("Redis cache connection established")
    except Exception as e:
        logger.error("Failed to connect to Redis", error=str(e))
        raise


async def get_cache() -> redis.Redis:
    """Get Redis cache client."""
    if redis_client is None:
        raise RuntimeError("Cache not initialized")
    return redis_client


async def get(key: str) -> Optional[str]:
    """Get value from cache."""
    try:
        cache = await get_cache()
        return await cache.get(key)
    except Exception as e:
        logger.error("Failed to get from cache", key=key, error=str(e))
        return None


async def set(key: str, value: Any, expire: Optional[int] = None) -> bool:
    """Set value in cache."""
    try:
        cache = await get_cache()
        await cache.set(key, value, ex=expire)
        return True
    except Exception as e:
        logger.error("Failed to set cache", key=key, error=str(e))
        return False


async def delete(key: str) -> bool:
    """Delete value from cache."""
    try:
        cache = await get_cache()
        await cache.delete(key)
        return True
    except Exception as e:
        logger.error("Failed to delete from cache", key=key, error=str(e))
        return False


async def exists(key: str) -> bool:
    """Check if key exists in cache."""
    try:
        cache = await get_cache()
        return await cache.exists(key) > 0
    except Exception as e:
        logger.error("Failed to check cache existence", key=key, error=str(e))
        return False
