from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_allocation_sum():
    response = client.get("/rebalance/config/allocation")
    assert response.status_code == 200
    assert abs(sum(response.json()["weights"].values()) - 1.0) < 1e-6

