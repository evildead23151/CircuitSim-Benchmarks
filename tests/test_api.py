"""Tests for API endpoints."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import numpy as np


@pytest.fixture
def client():
    """Create a test client with the FastAPI app."""
    from app.main import app
    with TestClient(app) as c:
        yield c


class TestRootEndpoint:
    def test_root_returns_200(self, client):
        r = client.get("/")
        assert r.status_code == 200
        data = r.json()
        assert "status" in data


class TestHealthEndpoint:
    def test_health_returns_ok(self, client):
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


class TestConfigEndpoint:
    def test_set_remote_url(self, client):
        r = client.post("/config/remote", json={"url": "http://test.example.com"})
        assert r.status_code == 200
        data = r.json()
        assert "status" in data

    def test_clear_remote_url(self, client):
        r = client.post("/config/remote", json={"url": ""})
        assert r.status_code == 200
        data = r.json()
        assert "local" in data["status"].lower()


class TestBenchmarkTopological:
    def test_valid_circuit(self, client):
        payload = {
            "stages": [
                {"tag": 1, "type": "R", "value": 100.0},
                {"tag": 1, "type": "L", "value": 0.001},
                {"tag": 1, "type": "C", "value": 1e-6},
            ],
            "frequency": 1000.0,
            "vin": 1.0,
        }
        r = client.post("/benchmark/topological", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "solver_vout" in data
        assert "ai_vout" in data
        assert data["solver_vout"] >= 0

    def test_invalid_input_returns_422(self, client):
        # Missing required fields
        r = client.post("/benchmark/topological", json={"stages": "not_a_list"})
        assert r.status_code == 422

    def test_empty_stages(self, client):
        r = client.post("/benchmark/topological", json={"stages": [], "frequency": 1000.0, "vin": 1.0})
        assert r.status_code == 200


class TestModelsEndpoints:
    def test_list_models(self, client):
        r = client.get("/models/list")
        assert r.status_code == 200
        data = r.json()
        assert "models" in data
        assert "active_model" in data
        assert isinstance(data["models"], list)

    def test_select_model_invalid(self, client):
        r = client.post("/models/select", json={"model_name": "nonexistent_model"})
        assert r.status_code == 404

    def test_select_model_valid(self, client):
        r = client.post("/models/select", json={"model_name": "random_forest"})
        assert r.status_code == 200
        assert r.json()["active_model"] == "random_forest"

    def test_compare_models(self, client):
        payload = {
            "stages": [{"tag": 1, "type": "R", "value": 100.0}],
            "frequency": 1000.0,
            "vin": 1.0,
        }
        r = client.post("/models/compare", json=payload)
        assert r.status_code == 200
        data = r.json()
        assert "models" in data
