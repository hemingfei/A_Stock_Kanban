"""Tests for health check endpoints."""
from unittest.mock import patch, MagicMock
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
