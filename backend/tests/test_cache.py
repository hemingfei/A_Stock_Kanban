"""Tests for cache module."""
import pytest
import time
from unittest.mock import patch, MagicMock, AsyncMock


def test_get_quote_key():
    """Test get_quote_key function."""
    from app.cache import get_quote_key
    assert get_quote_key("600519") == "quote:600519"


def test_get_quotes_key():
    """Test get_quotes_key function."""
    from app.cache import get_quotes_key
    key = get_quotes_key(["600519", "000001"])
    assert key.startswith("quotes:")
    # Order shouldn't matter
    key2 = get_quotes_key(["000001", "600519"])
    assert key == key2


def test_get_kline_key():
    """Test get_kline_key function."""
    from app.cache import get_kline_key
    assert get_kline_key("600519", "1d") == "kline:600519:1d"


def test_get_search_key():
    """Test get_search_key function."""
    from app.cache import get_search_key
    assert get_search_key("茅台") == "search:茅台"


@pytest.mark.asyncio
async def test_memory_cache_set_and_get():
    """Test memory cache fallback set and get."""
    from app.cache import set_cache, get_cache, _memory_cache, close_redis

    # Force no Redis
    await close_redis()
    with patch('app.cache.get_redis', return_value=None):
        # Clear memory cache first
        _memory_cache.clear()

        # Set cache
        await set_cache("test_key", "test_value", ttl=10)
        assert "test_key" in _memory_cache

        # Get cache
        value = await get_cache("test_key")
        assert value == "test_value"


@pytest.mark.asyncio
async def test_memory_cache_expired():
    """Test that expired cache entries are not returned."""
    from app.cache import set_cache, get_cache, _memory_cache, close_redis

    await close_redis()
    with patch('app.cache.get_redis', return_value=None):
        _memory_cache.clear()

        # Set cache with very short TTL
        await set_cache("expired_key", "expired_value", ttl=0)

        # Wait a bit
        time.sleep(0.01)

        # Should be expired
        value = await get_cache("expired_key")
        assert value is None


@pytest.mark.asyncio
async def test_memory_cache_delete():
    """Test deleting from memory cache."""
    from app.cache import set_cache, delete_cache, get_cache, _memory_cache, close_redis

    await close_redis()
    with patch('app.cache.get_redis', return_value=None):
        _memory_cache.clear()

        await set_cache("delete_me", "value", ttl=10)
        assert await get_cache("delete_me") == "value"

        await delete_cache("delete_me")
        assert await get_cache("delete_me") is None


@pytest.mark.asyncio
async def test_memory_cache_delete_pattern():
    """Test deleting cache by pattern."""
    from app.cache import set_cache, delete_cache_pattern, get_cache, _memory_cache, close_redis

    await close_redis()
    with patch('app.cache.get_redis', return_value=None):
        _memory_cache.clear()

        await set_cache("pattern:a", "value1", ttl=10)
        await set_cache("pattern:b", "value2", ttl=10)
        await set_cache("other:c", "value3", ttl=10)

        await delete_cache_pattern("pattern:*")

        assert await get_cache("pattern:a") is None
        assert await get_cache("pattern:b") is None
        assert await get_cache("other:c") == "value3"


@pytest.mark.asyncio
async def test_redis_client_fails_fallback_to_memory():
    """Test that when Redis fails, we fallback to memory cache."""
    from app.cache import set_cache, get_cache, _memory_cache, close_redis

    await close_redis()
    _memory_cache.clear()

    # Mock redis.from_url to raise an exception
    with patch('app.cache.redis.from_url') as mock_from_url:
        mock_from_url.side_effect = Exception("Redis not available")

        # This should use memory cache instead
        await set_cache("fallback_key", "fallback_value", ttl=10)
        value = await get_cache("fallback_key")
        assert value == "fallback_value"


@pytest.mark.asyncio
async def test_get_redis_cached():
    """Test that get_redis caches the client."""
    from app.cache import get_redis, close_redis, _redis_client

    await close_redis()

    # Mock redis.from_url
    with patch('app.cache.redis.from_url') as mock_from_url:
        mock_client = MagicMock()
        mock_client.close = AsyncMock()
        mock_from_url.return_value = mock_client

        # First call creates client
        client1 = await get_redis()
        # Second call returns cached client
        client2 = await get_redis()

        assert client1 is client2
        mock_from_url.assert_called_once()


@pytest.mark.asyncio
async def test_redis_operation_fails():
    """Test that Redis operation failures don't crash the app."""
    from app.cache import set_cache, get_cache, close_redis

    await close_redis()

    # Create a mock Redis client that fails operations
    mock_client = MagicMock()
    mock_client.setex = AsyncMock(side_effect=Exception("Redis error"))
    mock_client.get = AsyncMock(side_effect=Exception("Redis error"))
    mock_client.close = AsyncMock()

    with patch('app.cache.get_redis', return_value=mock_client):
        # These should not raise exceptions
        await set_cache("error_key", "error_value", ttl=10)
        value = await get_cache("error_key")
        # Falls back to no cache but doesn't crash
        assert True  # Just check it completes
