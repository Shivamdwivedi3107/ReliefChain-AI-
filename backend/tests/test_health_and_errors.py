import pytest
from fastapi.testclient import TestClient


def test_health_probes(client: TestClient):
    # Root Health
    res_root = client.get("/health")
    assert res_root.status_code == 200
    assert res_root.json()["status"] in ["healthy", "degraded"]

    # Liveness
    res_live = client.get("/health/live")
    assert res_live.status_code == 200
    assert res_live.json()["status"] == "alive"

    # Readiness
    res_ready = client.get("/health/ready")
    assert res_ready.status_code in [200, 503]
    ready_data = res_ready.json()
    assert "status" in ready_data
    assert "database" in ready_data
    assert "ai_model" in ready_data
    assert "ledger" in ready_data


def test_standardized_error_format(client: TestClient, admin_token: str):
    headers = {"Authorization": f"Bearer {admin_token}"}
    
    # 404 Not Found on mission
    res_404 = client.get("/api/v1/missions/non-existent-uuid-12345", headers=headers)
    assert res_404.status_code == 404

    # 422 Validation Error
    res_422 = client.post("/api/v1/relief-requests", json={"invalid": "payload"}, headers=headers)
    assert res_422.status_code == 422
