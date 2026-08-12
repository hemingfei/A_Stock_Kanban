"""Tests for authentication endpoints."""


def _register_and_login(client, username="testuser", password="testpass123"):
    """Helper to register and login a user, returning tokens."""
    # Register
    reg_resp = client.post(
        "/api/v1/auth/register",
        json={"username": username, "password": password}
    )
    assert reg_resp.status_code == 200
    reg_data = reg_resp.json()
    assert reg_data["success"] is True

    # Or login if already exists
    login_resp = client.post(
        "/api/v1/auth/login",
        data={"username": username, "password": password}
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert login_data["success"] is True

    return {
        "access_token": login_data["data"]["access_token"],
        "refresh_token": login_data["data"]["refresh_token"],
        "auth_headers": {"Authorization": "Bearer {}".format(login_data["data"]["access_token"])}
    }


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
        json={"username": "loginuser", "password": "testpass123"}
    )

    # Login
    response = client.post(
        "/api/v1/auth/login",
        data={"username": "loginuser", "password": "testpass123"}
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
    tokens = _register_and_login(client, "meuser")
    response = client.get(
        "/api/v1/auth/me",
        headers=tokens["auth_headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "meuser"


def test_get_current_user_no_auth(client):
    """Test getting current user without auth fails."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401


def test_token_refresh(client):
    """Test token refresh functionality."""
    tokens = _register_and_login(client, "refreshuser")
    response = client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": tokens["refresh_token"]}
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


def test_logout(client):
    """Test logout functionality."""
    tokens = _register_and_login(client, "logoutuser")
    response = client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=tokens["auth_headers"]
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True