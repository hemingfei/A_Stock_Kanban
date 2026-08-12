"""Tests for health check endpoints."""


def test_root_endpoint(client):
    """Test the root endpoint returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "name" in data["data"]
    assert "version" in data["data"]
    assert "docs" in data["data"]


def test_health_endpoint(client):
    """Test the main health endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_health_live_endpoint(client):
    """Test the liveness probe endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


def test_openapi_docs_available(client):
    """Test that OpenAPI docs are available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()