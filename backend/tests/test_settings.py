"""Tests for user settings endpoints."""


class TestGetSettings:
    """Tests for getting user settings."""

    def test_get_settings_first_time(self, client, auth_headers):
        """Test getting settings for the first time (should create defaults)."""
        response = client.get(
            "/api/v1/settings",
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["refresh_interval"] == 5
        assert data["data"]["theme"] == "light"

    def test_get_settings_existing(self, client, auth_headers, test_user):
        """Test getting existing settings."""
        # First get should create them
        client.get("/api/v1/settings", headers=auth_headers)
        # Second get should return the same
        response = client.get("/api/v1/settings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_get_settings_no_auth(self, client):
        """Test getting settings without authentication."""
        response = client.get("/api/v1/settings")
        assert response.status_code == 401


class TestUpdateSettings:
    """Tests for updating user settings."""

    def test_update_settings_all_fields(self, client, auth_headers):
        """Test updating all settings fields."""
        response = client.put(
            "/api/v1/settings",
            json={
                "refresh_interval": 10,
                "data_sources": '["akshare"]',
                "theme": "dark"
            },
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["refresh_interval"] == 10
        assert data["data"]["theme"] == "dark"

    def test_update_settings_partial_fields(self, client, auth_headers):
        """Test updating only some settings fields."""
        # First get settings to ensure they exist
        client.get("/api/v1/settings", headers=auth_headers)

        # Update only theme
        response = client.put(
            "/api/v1/settings",
            json={"theme": "dark"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["theme"] == "dark"
        # Other fields should remain unchanged
        assert data["data"]["refresh_interval"] == 5

    def test_update_settings_refresh_interval_min(self, client, auth_headers):
        """Test updating refresh_interval to minimum (1)."""
        response = client.put(
            "/api/v1/settings",
            json={"refresh_interval": 1},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["refresh_interval"] == 1

    def test_update_settings_refresh_interval_max(self, client, auth_headers):
        """Test updating refresh_interval to maximum (60)."""
        response = client.put(
            "/api/v1/settings",
            json={"refresh_interval": 60},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["refresh_interval"] == 60

    def test_update_settings_refresh_interval_too_small(self, client, auth_headers):
        """Test updating refresh_interval to too small (0)."""
        response = client.put(
            "/api/v1/settings",
            json={"refresh_interval": 0},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_settings_refresh_interval_too_large(self, client, auth_headers):
        """Test updating refresh_interval to too large (61)."""
        response = client.put(
            "/api/v1/settings",
            json={"refresh_interval": 61},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_settings_theme_light(self, client, auth_headers):
        """Test updating theme to light."""
        response = client.put(
            "/api/v1/settings",
            json={"theme": "light"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["theme"] == "light"

    def test_update_settings_theme_dark(self, client, auth_headers):
        """Test updating theme to dark."""
        response = client.put(
            "/api/v1/settings",
            json={"theme": "dark"},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["theme"] == "dark"

    def test_update_settings_theme_invalid(self, client, auth_headers):
        """Test updating theme to invalid value."""
        response = client.put(
            "/api/v1/settings",
            json={"theme": "invalid"},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_settings_no_auth(self, client):
        """Test updating settings without authentication."""
        response = client.put(
            "/api/v1/settings",
            json={"theme": "dark"}
        )
        assert response.status_code == 401
