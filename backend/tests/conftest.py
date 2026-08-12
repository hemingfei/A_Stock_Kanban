import pytest
import asyncio
import tempfile
from pathlib import Path
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient

from app.database import Base, get_session
from main import app
from app.config import get_settings
from app.models import User, UserSetting, Board, Stock
from app.auth import get_password_hash, create_access_token

# Override settings for tests
test_settings = get_settings()


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create a test database using temp file."""
    # Create temp file
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name

    try:
        db_url = f"sqlite+aiosqlite:///{db_path}"
        engine = create_async_engine(db_url, connect_args={"check_same_thread": False})

        # Create tables
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        # Create session
        async_session = sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        async with async_session() as session:
            yield session

        await engine.dispose()
    finally:
        # Clean up
        try:
            Path(db_path).unlink(missing_ok=True)
        except:
            pass


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with DB session override."""
    async def _override_get_session():
        yield test_db

    app.dependency_overrides[get_session] = _override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()


@pytest.fixture
async def test_user(test_db):
    """Create a test user in database."""
    hashed_password = get_password_hash("testpass123")
    user = User(
        username="testuser",
        password_hash=hashed_password
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    # Create default settings
    settings = UserSetting(user_id=user.id)
    test_db.add(settings)
    await test_db.commit()

    return user


@pytest.fixture
async def auth_headers(test_user):
    """Get authentication headers with access token."""
    access_token = create_access_token(data={"sub": test_user.id})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def test_board(test_db, test_user):
    """Create a test board for the test user."""
    from app.models import Board
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
    """Create a test stock in the test board."""
    from app.models import Stock
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
    from app.models import User, UserSetting
    hashed_password = get_password_hash("testpass123")
    user = User(
        username="testuser2",
        password_hash=hashed_password
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)

    # Create default settings
    settings = UserSetting(user_id=user.id)
    test_db.add(settings)
    await test_db.commit()

    return user


@pytest.fixture
async def auth_headers_user2(test_user2):
    """Get authentication headers for the second test user."""
    access_token = create_access_token(data={"sub": test_user2.id})
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
async def test_board_user2(test_db, test_user2):
    """Create a test board for the second test user."""
    from app.models import Board
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
async def test_user_no_settings(test_db):
    """Create a test user WITHOUT default settings (for testing settings creation)."""
    hashed_password = get_password_hash("testpass123")
    user = User(
        username="testusernosettings",
        password_hash=hashed_password
    )
    test_db.add(user)
    await test_db.commit()
    await test_db.refresh(user)
    return user


@pytest.fixture
async def auth_headers_no_settings(test_user_no_settings):
    """Get authentication headers for user without settings."""
    access_token = create_access_token(data={"sub": test_user_no_settings.id})
    return {"Authorization": f"Bearer {access_token}"}