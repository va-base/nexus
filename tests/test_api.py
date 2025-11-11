"""Test API endpoints"""
import pytest
from fastapi.testclient import TestClient
from nexus.api.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health():
    """Test health endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_list_hypotheses():
    """Test list hypotheses endpoint"""
    response = client.get("/api/hypotheses/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_evidence():
    """Test list evidence endpoint"""
    response = client.get("/api/evidence/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_current_beliefs():
    """Test current beliefs endpoint"""
    response = client.get("/api/beliefs/current")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
