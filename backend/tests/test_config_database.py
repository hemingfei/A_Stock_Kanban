"""Tests for config and database modules."""


def test_cors_origins_list_valid():
    """Test cors_origins_list with valid JSON."""
    from app.config import Settings
    settings = Settings(cors_origins='["http://a.com","http://b.com"]')
    assert settings.cors_origins_list == ["http://a.com", "http://b.com"]


def test_cors_origins_list_invalid_json():
    """Test cors_origins_list with invalid JSON falls back to default."""
    from app.config import Settings
    settings = Settings(cors_origins='not-json')
    assert settings.cors_origins_list == ["http://localhost:3000", "http://localhost:5173"]


def test_get_settings_cached():
    """Test that get_settings is cached."""
    from app.config import get_settings
    settings1 = get_settings()
    settings2 = get_settings()
    assert settings1 is settings2


def test_settings_env_override():
    """Test that settings can be overridden."""
    from app.config import Settings
    settings = Settings(debug=True, env="test")
    assert settings.debug is True
    assert settings.env == "test"


def test_settings_defaults():
    """Test default settings values."""
    from app.config import Settings
    settings = Settings()
    assert settings.jwt_algorithm == "HS256"
    assert settings.jwt_access_token_expire_hours == 2
    assert settings.jwt_refresh_token_expire_days == 7


def test_get_session_exists():
    """Test get_session function exists."""
    from app.database import get_session
    assert callable(get_session)


def test_init_db_exists():
    """Test init_db function exists."""
    from app.database import init_db
    assert callable(init_db)
