import pytest
from fastapi.testclient import TestClient


def test_audit_logs_rbac_and_queries(client: TestClient, admin_token: str, citizen_token: str):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    cit_headers = {"Authorization": f"Bearer {citizen_token}"}

    # 1. Admin should have access to audit logs
    admin_res = client.get("/api/v1/audit-logs", headers=admin_headers)
    assert admin_res.status_code == 200
    data = admin_res.json()
    assert "total" in data
    assert "data" in data

    # 2. Non-admin (Citizen) must be rejected with 403 Forbidden
    cit_res = client.get("/api/v1/audit-logs", headers=cit_headers)
    assert cit_res.status_code == 403

    # 3. Unauthenticated request must be rejected with 401
    unauth_res = client.get("/api/v1/audit-logs")
    assert unauth_res.status_code == 401
