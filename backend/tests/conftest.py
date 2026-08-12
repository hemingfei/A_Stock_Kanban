import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_session
from app.main import app
from app.config import get_settings
from app.models import User, Board, Stock, UserSetting, AuditLog
from app.auth import get_password_hash, create_access_token, create_refresh_token
from datetime import timedelta

# Override settings for tests
test_settings = get_settings()
test_settings.database_url = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create a test database."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client."""
    async def _override_get_session():
        yield test_db

    app.dependency_overrides[get_session] = _override_get_session
    return TestClient(app)


@pytest.fixture
def test_user_data():
    """Test user data."""
    return {
        "username": "testuser",
        "password": "testpass123"
    }


@pytest.fixture
async def test_user(test_db, test_user_data):
    """Create a test user in database."""
    hashed_password = get_password_hash(test_user_data["password"])
    user = User(
        username=test_user_data["username"],
        password_hash=hashed_password
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    # Create default settings - use a separate commit to ensure user exists
    settings = UserSetting(user_id=user.id)
    test_db.add(settings)
    await test_db.commit()

    return user


@pytest.fixture
def auth_headers(test_user, test_user_data):
    """Get authentication headers with access token."""
    access_token = create_access_token(
        data={"sub": test_user.id},
        expires_delta=timedelta(hours=2)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def refresh_token_headers(test_user):
    """Get refresh token."""
    refresh_token = create_refresh_token(data={"sub": test_user.id})
    return refresh_token


@pytest.fixture
async def test_board(test_db, test_user):
    """Create a test board."""
    board = Board(
        user_id=test_user.id,
        name="Test Board",
        sort_order=0
    )
    test_db.add(board)
    await test_db.commit()
    await test_db.refresh(board)
    return board


@pytest.fixture
async def test_stock(test_db, test_board):
    """Create a test stock in board."""
    stock = Stock(
        board_id=test_board.id,
        code="600519",
        name="贵州茅台",
        sort_order=0
    )
    test_db.add(stock)
    await test_db.commit()
    await test_db.refresh(stock)
    return stock


@pytest.fixture
async def test_user2(test_db):
    """Create a second test user for permission tests."""
    hashed_password = get_password_hash("password456")
    user = User(
        username="otheruser",
        password_hash=hashed_password
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    settings = UserSetting(user_id=user.id)
    test_db.add(settings)
    await test_db.commit()

    return user


@pytest.fixture
def auth_headers_user2(test_user2):
    """Get authentication headers for user2."""
    access_token = create_access_token(
        data={"sub": test_user2.id},
        expires_delta=timedelta(hours=2)
    )
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def test_board_user2(test_db, test_user2):
    """Create a board belonging to user2."""
    board = Board(
        user_id=test_user2.id,
        name="User2's Board",
        sort_order=0
    )
    test_db.add(board)
    await test_db.commit()
    await test_db.refresh(board)
    return board


@pytest.fixture
async def audit_logs(test_db):
    """Get all audit logs."""
    from sqlalchemy import select
    result = await test_db.execute(select(AuditLog))
    return result.scalars().all()
