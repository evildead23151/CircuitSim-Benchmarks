import pytest


TOPO_PAYLOAD = {
    "stages": [
        {"tag": 1, "type": "R", "value": 100.0},
        {"tag": 2, "type": "C", "value": 1e-6},
    ],
    "frequency": 1000.0,
    "vin": 1.0,
}


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert "status" in data


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_ready(client):
    r = client.get("/ready")
    assert r.status_code == 200
    assert r.json()["status"] == "ready"


def test_benchmark_topological(client):
    r = client.post("/benchmark/topological", json=TOPO_PAYLOAD)
    assert r.status_code == 200
    data = r.json()
    assert "solver_vout" in data
    assert "ai_vout" in data
    assert data["solver_vout"] >= 0.0


def test_models_list(client):
    r = client.get("/models/list")
    assert r.status_code == 200
    data = r.json()
    assert "models" in data
    names = [m["name"] for m in data["models"]]
    assert "random_forest" in names
    assert "ensemble" in names


def test_models_compare(client):
    r = client.post("/models/compare", json=TOPO_PAYLOAD)
    assert r.status_code == 200
    results = r.json()
    assert isinstance(results, list)
    assert len(results) >= 1
    for item in results:
        assert "model_name" in item
        assert "vout" in item
        assert "latency_ms" in item
