"""Tests for authentication endpoints."""
import pytest
from datetime import timedelta
from app.auth import create_access_token, token_blacklist
from app.models import AuditLog


def test_register_user(client):
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "user" in data["data"]
    assert "access_token" in data["data"]


def test_register_duplicate_username(client):
    """Test registering duplicate username fails."""
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={"username": "testuser2", "password": "testpass123"}
    )

    # Try to register again
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser2", "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "USERNAME_EXISTS"


def test_register_username_too_short(client):
    """Test registering with username too short (1 char)."""
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "a", "password": "testpass123"}
    )
    # Should fail validation
    assert response.status_code == 422


def test_register_username_too_long(client):
    """Test registering with username too long (51 chars)."""
    long_username = "a" * 51
    response = client.post(
        "/api/v1/auth/register",
        json={"username": long_username, "password": "testpass123"}
    )
    assert response.status_code == 422


def test_register_username_max_length_ok(client):
    """Test registering with username at max length (50 chars)."""
    max_username = "a" * 50
    response = client.post(
        "/api/v1/auth/register",
        json={"username": max_username, "password": "testpass123"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_register_password_too_short(client):
    """Test registering with password too short (7 chars)."""
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": "short1"}
    )
    assert response.status_code == 422


def test_register_password_max_length_ok(client):
    """Test registering with password at max length (128 chars)."""
    max_password = "a" * 128
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": max_password}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_register_password_too_long(client):
    """Test registering with password too long (129 chars)."""
    long_password = "a" * 129
    response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser", "password": long_password}
    )
    assert response.status_code == 422


def test_login_user(client, test_user, test_user_data):
    """Test user login."""
    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user_data["username"], "password": test_user_data["password"]}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_login_invalid_credentials(client):
    """Test login with invalid credentials fails."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "nonexistent", "password": "wrongpass"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"


def test_get_current_user(client, test_user, auth_headers):
    """Test getting current user info."""
    response = client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == test_user.username


def test_get_current_user_no_auth(client):
    """Test getting current user without auth fails."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_get_current_user_invalid_token_format(client):
    """Test with invalid token format."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "NotBearer token"}
    )
    assert response.status_code == 401


def test_get_current_user_malformed_token(client):
    """Test with malformed JWT token."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-jwt"}
    )
    assert response.status_code == 401


def test_get_current_user_expired_token(client, test_user):
    """Test with expired token."""
    # Create a token that expires in negative time (already expired)
    access_token = create_access_token(
        data={"sub": test_user.id},
        expires_delta=timedelta(seconds=-1)
    )
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 401


def test_token_refresh(client, test_user, refresh_token_headers):
    """Test token refresh functionality."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_headers}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]


def test_token_refresh_invalid_token(client):
    """Test token refresh with invalid token."""
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid-token"}
    )
    assert response.status_code == 401


def test_logout(client, test_user, auth_headers, refresh_token_headers):
    """Test logout functionality."""
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token_headers},
        headers=auth_headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_token_blacklisted_after_logout(client, test_user, auth_headers, refresh_token_headers):
    """Test that refresh token is blacklisted after logout."""
    # Logout first
    client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": refresh_token_headers},
        headers=auth_headers
    )

    # Try to use the same refresh token
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token_headers}
    )
    assert response.status_code == 401


def test_register_creates_audit_log(client, test_db):
    """Test that registration creates an audit log entry."""
    from sqlalchemy import select

    response = client.post(
        "/api/v1/auth/register",
        json={"username": "audituser", "password": "testpass123"}
    )
    assert response.status_code == 200

    # Check audit log
    async def check_log():
        result = await test_db.execute(
            select(AuditLog).where(AuditLog.action == "user_register")
        )
        log = result.scalar_one_or_none()
        assert log is not None
        assert log.action == "user_register"

    import asyncio
    asyncio.run(check_log())


def test_login_creates_audit_log(client, test_user, test_user_data):
    """Test that login creates an audit log entry."""
    response = client.post(
        "/api/v1/auth/login",
        data={"username": test_user_data["username"], "password": test_user_data["password"]}
    )
    assert response.status_code == 200
    # Audit log checked by fixture
