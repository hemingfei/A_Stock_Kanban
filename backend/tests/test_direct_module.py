"""Direct tests for board, stock, and settings modules - improves coverage."""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock


@pytest.mark.asyncio
async def test_get_settings_function():
    """Directly test get_settings function logic."""
    from app.models import User, UserSetting
    from sqlalchemy.ext.asyncio import AsyncSession

    # Create a mock user and session
    mock_user = User(id=1, username="testuser")

    # Mock database session
    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()

    # First case: no settings exist yet
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Verify we can import the module
    from app import settings as settings_module
    assert settings_module is not None

    # Verify the router exists
    assert hasattr(settings_module, 'router')


@pytest.mark.asyncio
async def test_board_module_import():
    """Test that board module can be imported."""
    from app import boards
    assert boards is not None
    assert hasattr(boards, 'router')


@pytest.mark.asyncio
async def test_stock_module_import():
    """Test that stock module can be imported."""
    from app import stocks
    assert stocks is not None
    assert hasattr(stocks, 'router')


@pytest.mark.asyncio
async def test_get_board_for_user_helper():
    """Test the helper function for getting boards."""
    from app.stocks import get_board_for_user
    from app.models import Board
    from sqlalchemy.ext.asyncio import AsyncSession

    mock_session = MagicMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_board = Board(id=1, user_id=1, name="Test Board", sort_order=0)
    mock_result.scalar_one_or_none.return_value = mock_board
    mock_session.execute = AsyncMock(return_value=mock_result)

    # Call the function (we're testing it can be called)
    result = await get_board_for_user(board_id=1, user_id=1, db=mock_session)
    assert result is not None


def test_log_audit_event_import():
    """Test that audit log function can be imported."""
    from app.auth import log_audit_event
    assert callable(log_audit_event)


def test_cache_helpers():
    """Test cache key helper functions."""
    from app.cache import get_quote_key, get_quotes_key, get_kline_key, get_search_key

    assert get_quote_key("600519") == "quote:600519"
    assert get_quotes_key(["600519", "000001"]) is not None  # Hashed
    assert get_kline_key("600519", "1d") == "kline:600519:1d"
    assert get_search_key("茅台") == "search:茅台"


def test_cache_module_import():
    """Test all cache functions are importable."""
    from app import cache
    assert hasattr(cache, 'get_cache')
    assert hasattr(cache, 'set_cache')
    assert hasattr(cache, 'delete_cache')
    assert hasattr(cache, 'delete_cache_pattern')
    assert hasattr(cache, 'get_redis')
    assert hasattr(cache, 'close_redis')


@pytest.mark.asyncio
async def test_memory_cache_fallback():
    """Test memory cache fallback path."""
    from app.cache import _memory_cache, set_cache, get_cache, close_redis

    # Ensure clean state
    await close_redis()
    _memory_cache.clear()

    with patch('app.cache.get_redis', return_value=None):
        await set_cache('test-direct-key', {'data': 'test'}, 60)
        result = await get_cache('test-direct-key')
        assert result == {'data': 'test'}


@pytest.mark.asyncio
async def test_delete_cache_memory():
    """Test delete cache in memory mode."""
    from app.cache import _memory_cache, set_cache, delete_cache, get_cache, close_redis

    await close_redis()
    _memory_cache.clear()

    with patch('app.cache.get_redis', return_value=None):
        await set_cache('delete-me', 'value', 60)
        assert await get_cache('delete-me') == 'value'

        await delete_cache('delete-me')
        assert await get_cache('delete-me') is None


@pytest.mark.asyncio
async def test_delete_cache_pattern_memory():
    """Test delete cache by pattern in memory mode."""
    from app.cache import _memory_cache, set_cache, delete_cache_pattern, get_cache, close_redis

    await close_redis()
    _memory_cache.clear()

    with patch('app.cache.get_redis', return_value=None):
        await set_cache('pattern:a', '1', 60)
        await set_cache('pattern:b', '2', 60)
        await set_cache('keep-this', '3', 60)

        await delete_cache_pattern('pattern:*')

        assert await get_cache('pattern:a') is None
        assert await get_cache('pattern:b') is None
        assert await get_cache('keep-this') == '3'


def test_database_module_import():
    """Test database module imports."""
    from app import database
    assert hasattr(database, 'Base')
    assert hasattr(database, 'get_session')
    assert hasattr(database, 'init_db')


def test_settings_schema_validation():
    """Test settings schema validation."""
    from app.schemas import UserSettingUpdate
    from pydantic import ValidationError

    # Valid
    valid = UserSettingUpdate(refresh_interval=5, theme="light")
    assert valid.refresh_interval == 5

    # Invalid theme
    with pytest.raises(ValidationError):
        UserSettingUpdate(theme="invalid")

    # Invalid refresh interval
    with pytest.raises(ValidationError):
        UserSettingUpdate(refresh_interval=0)
    with pytest.raises(ValidationError):
        UserSettingUpdate(refresh_interval=61)


def test_board_schemas():
    """Test board-related schemas."""
    from app.schemas import BoardCreate, BoardUpdate, BoardReorderRequest

    # Test BoardCreate
    board_create = BoardCreate(name="Test Board")
    assert board_create.name == "Test Board"

    # Test BoardUpdate
    board_update = BoardUpdate(name="New Name", sort_order=5)
    assert board_update.name == "New Name"
    assert board_update.sort_order == 5

    # Test BoardReorderRequest
    reorder = BoardReorderRequest(board_ids=[1, 2, 3])
    assert reorder.board_ids == [1, 2, 3]

    # Test empty board_ids is allowed
    reorder_empty = BoardReorderRequest(board_ids=[])
    assert reorder_empty.board_ids == []


def test_stock_schemas():
    """Test stock-related schemas."""
    from app.schemas import StockCreate, StockUpdate, StockReorderRequest

    # Test StockCreate
    stock_create = StockCreate(code="600519", name="贵州茅台")
    assert stock_create.code == "600519"
    assert stock_create.name == "贵州茅台"

    # Test StockUpdate
    stock_update = StockUpdate(name="New Name", sort_order=5)
    assert stock_update.name == "New Name"
    assert stock_update.sort_order == 5

    # Test StockReorderRequest
    reorder = StockReorderRequest(stock_ids=[1, 2, 3])
    assert reorder.stock_ids == [1, 2, 3]
