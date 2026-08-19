import pytest
from fastapi.testclient import TestClient


def test_citizen_mission_isolation(client: TestClient, citizen_token: str, admin_token: str, relief_request_data):
    cit_headers = {"Authorization": f"Bearer {citizen_token}"}
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Citizen 1 creates request
    res = client.post("/api/v1/relief-requests", json=relief_request_data, headers=cit_headers)
    assert res.status_code == 201
    mission_id = res.json()["id"]

    # Register Citizen 2
    client.post("/api/v1/auth/register", json={
        "email": "citizen2@reliefchain.ai",
        "full_name": "Citizen Two",
        "password": "SecurePassword123!",
        "role": "citizen",
    })
    token2 = client.post("/api/v1/auth/login", json={
        "email": "citizen2@reliefchain.ai",
        "password": "SecurePassword123!",
    }).json()["access_token"]
    cit2_headers = {"Authorization": f"Bearer {token2}"}

    # Citizen 2 should NOT have permission to access Citizen 1's mission details
    view_res = client.get(f"/api/v1/missions/{mission_id}", headers=cit2_headers)
    assert view_res.status_code == 403

    # Citizen 2 should NOT have permission to cancel Citizen 1's mission
    cancel_res = client.patch(
        f"/api/v1/missions/{mission_id}/status",
        json={"new_status": "cancelled"},
        headers=cit2_headers,
    )
    assert cancel_res.status_code == 403


def test_volunteer_permissions_on_missions(client: TestClient, volunteer_token: str, admin_token: str, relief_request_data):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    vol_headers = {"Authorization": f"Bearer {volunteer_token}"}

    # Admin creates and assigns mission
    res = client.post("/api/v1/relief-requests", json=relief_request_data, headers=admin_headers)
    mission_id = res.json()["id"]

    # Volunteer cannot mark mission completed directly (must follow lifecycle)
    illegal_res = client.patch(
        f"/api/v1/missions/{mission_id}/status",
        json={"new_status": "completed"},
        headers=vol_headers,
    )
    assert illegal_res.status_code == 403


def test_mission_filters_and_sorting(client: TestClient, admin_token: str, relief_request_data):
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Create two requests with different parameters
    client.post("/api/v1/relief-requests", json=relief_request_data, headers=admin_headers)
    
    data2 = dict(relief_request_data)
    data2["location_name"] = "Southern Hills Sector 9"
    data2["disaster_type"] = "earthquake"
    client.post("/api/v1/relief-requests", json=data2, headers=admin_headers)

    # Filter by status
    pending_res = client.get("/api/v1/missions?status=pending", headers=admin_headers)
    assert pending_res.status_code == 200
    assert pending_res.json()["total"] >= 2
