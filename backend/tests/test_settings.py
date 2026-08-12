"""Tests for user settings endpoints - improved for better coverage."""


class TestGetSettings:
    """Tests for getting user settings."""

    def test_get_settings_first_time_creates_defaults(self, client, auth_headers_no_settings, test_user_no_settings):
        """Test getting settings for the first time - should create defaults."""
        response = client.get("/api/v1/settings", headers=auth_headers_no_settings)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["refresh_interval"] == 5
        assert data["data"]["theme"] == "light"
        # Verify settings has an ID (was created)
        assert data["data"]["id"] is not None

    def test_get_settings_existing(self, client, auth_headers):
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

    def test_update_settings_user_without_settings_creates_them(self, client, auth_headers_no_settings):
        """Test updating settings for a user without existing settings - should create them."""
        response = client.put(
            "/api/v1/settings",
            json={"theme": "dark"},
            headers=auth_headers_no_settings
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["theme"] == "dark"
        assert data["data"]["id"] is not None

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
        # First get to ensure settings exist
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
        """Test updating refresh_interval to too small (0) - should fail validation."""
        response = client.put(
            "/api/v1/settings",
            json={"refresh_interval": 0},
            headers=auth_headers
        )
        assert response.status_code == 422

    def test_update_settings_refresh_interval_too_large(self, client, auth_headers):
        """Test updating refresh_interval to too large (61) - should fail validation."""
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
        """Test updating theme to invalid value - should fail validation."""
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

    def test_update_only_data_sources(self, client, auth_headers):
        """Test updating only data_sources field."""
        response = client.put(
            "/api/v1/settings",
            json={"data_sources": '["tushare"]'},
            headers=auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestSettingsCompleteFlow:
    """Test complete CRUD flow for settings."""

    def test_complete_settings_flow(self, client, auth_headers_no_settings):
        """Test full cycle: create, update, verify, update again."""
        # 1. Get (creates defaults)
        resp1 = client.get("/api/v1/settings", headers=auth_headers_no_settings)
        assert resp1.status_code == 200
        data1 = resp1.json()["data"]
        assert data1["theme"] == "light"
        settings_id = data1["id"]

        # 2. Update to dark
        resp2 = client.put(
            "/api/v1/settings",
            json={"theme": "dark"},
            headers=auth_headers_no_settings
        )
        assert resp2.status_code == 200
        data2 = resp2.json()["data"]
        assert data2["theme"] == "dark"
        assert data2["id"] == settings_id  # Same ID

        # 3. Get again to verify persistence
        resp3 = client.get("/api/v1/settings", headers=auth_headers_no_settings)
        assert resp3.status_code == 200
        data3 = resp3.json()["data"]
        assert data3["theme"] == "dark"
        assert data3["id"] == settings_id

        # 4. Update back to light
        resp4 = client.put(
            "/api/v1/settings",
            json={"theme": "light"},
            headers=auth_headers_no_settings
        )
        assert resp4.status_code == 200
        data4 = resp4.json()["data"]
        assert data4["theme"] == "light"
