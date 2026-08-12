"""Tests for authentication endpoints."""


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


def test_login_user(client):
    """Test user login."""
    # Register first
    client.post(
        "/api/v1/auth/register",
        json={"username": "testuser3", "password": "testpass123"}
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "testuser3", "password": "testpass123"}
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


def test_get_current_user(client):
    """Test getting current user info."""
    # Register and login
    register_response = client.post(
        "/api/v1/auth/register",
        json={"username": "testuser4", "password": "testpass123"}
    )
    token = register_response.json()["data"]["access_token"]

    # Get current user
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "testuser4"


def test_get_current_user_no_auth(client):
    """Test getting current user without auth fails."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
