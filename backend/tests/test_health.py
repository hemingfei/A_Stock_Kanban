"""Tests for health check endpoints."""
from unittest.mock import patch, MagicMock, AsyncMock
import pytest


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
    assert "status" in data["data"]
    assert "database" in data["data"]
    assert "redis" in data["data"]
    assert "datasource" in data["data"]
    assert "uptime" in data["data"]


def test_health_live_endpoint(client):
    """Test the liveness probe endpoint."""
    response = client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "status" in data["data"]


def test_health_ready_endpoint(client):
    """Test the readiness probe endpoint."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert "data" in data
    assert "status" in data["data"]
    assert "checks" in data["data"]


def test_openapi_docs_available(client):
    """Test that OpenAPI docs are available."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert "openapi" in response.json()
    assert "info" in response.json()
    assert "paths" in response.json()


def test_health_ready_with_database_error():
    """Test readiness probe when database has an error."""
    from main import app
    from fastapi.testclient import TestClient
    from app.database import get_session

    # Create a mock session that raises an error
    async def mock_get_session_error():
        mock_session = MagicMock()
        mock_execute = AsyncMock(side_effect=Exception("DB Connection Failed"))
        mock_session.execute = mock_execute
        yield mock_session

    app.dependency_overrides[get_session] = mock_get_session_error
    try:
        client = TestClient(app)
        response = client.get("/health/ready")
        # Should still return 200 but with check status
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert "data" in data
    finally:
        app.dependency_overrides.pop(get_session, None)
