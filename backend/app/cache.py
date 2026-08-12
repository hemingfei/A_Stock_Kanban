from typing import Optional, Any
import json
import redis.asyncio as redis
from datetime import timedelta
from .config import get_settings

settings = get_settings()

# Global Redis client
_redis_client: Optional[redis.Redis] = None


async def get_redis() -> redis.Redis:
    """Get or create Redis client."""
    global _redis_client
    if _redis_client is None:
        try:
            _redis_client = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        except Exception:
            # If Redis is not available, use a dummy in-memory cache
            _redis_client = None
    return _redis_client


async def close_redis():
    """Close Redis connection."""
    global _redis_client
    if _redis_client:
        await _redis_client.close()
        _redis_client = None


# In-memory fallback cache
_memory_cache: dict[str, tuple[Any, float]] = {}


async def get_cache(key: str) -> Optional[Any]:
    """Get a value from cache."""
    redis_client = await get_redis()

    if redis_client:
        try:
            data = await redis_client.get(key)
            if data:
                return json.loads(data)
        except Exception:
            pass
    else:
        # Fallback to in-memory cache
        if key in _memory_cache:
            value, expire_time = _memory_cache[key]
            import time
            if time.time() < expire_time:
                return value
            else:
                del _memory_cache[key]

    return None


async def set_cache(key: str, value: Any, ttl: int = 300):
    """Set a value in cache with TTL (seconds)."""
    redis_client = await get_redis()
    data = json.dumps(value, ensure_ascii=False)

    if redis_client:
        try:
            await redis_client.setex(key, ttl, data)
        except Exception:
            pass
    else:
        # Fallback to in-memory cache
        import time
        expire_time = time.time() + ttl
        _memory_cache[key] = (value, expire_time)


async def delete_cache(key: str):
    """Delete a value from cache."""
    redis_client = await get_redis()

    if redis_client:
        try:
            await redis_client.delete(key)
        except Exception:
            pass
    else:
        if key in _memory_cache:
            del _memory_cache[key]


async def delete_cache_pattern(pattern: str):
    """Delete all keys matching a pattern."""
    redis_client = await get_redis()

    if redis_client:
        try:
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
        except Exception:
            pass
    else:
        # Fallback to in-memory cache
        import re
        pattern_re = re.compile(pattern.replace("*", ".*"))
        keys_to_delete = [k for k in _memory_cache if pattern_re.match(k)]
        for k in keys_to_delete:
            del _memory_cache[k]


def get_quote_key(code: str) -> str:
    """Get cache key for a stock quote."""
    return f"quote:{code}"


def get_quotes_key(codes: list[str]) -> str:
    """Get cache key for batch quotes."""
    import hashlib
    codes_str = ",".join(sorted(codes))
    hash_val = hashlib.md5(codes_str.encode()).hexdigest()
    return f"quotes:{hash_val}"


def get_kline_key(code: str, period: str) -> str:
    """Get cache key for K-line data."""
    return f"kline:{code}:{period}"


def get_search_key(keyword: str) -> str:
    """Get cache key for search results."""
    return f"search:{keyword}"
