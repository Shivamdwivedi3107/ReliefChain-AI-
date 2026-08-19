import pytest
from fastapi.testclient import TestClient
from app.models.relief_request import ReliefRequest


def test_mission_lifecycle_and_transitions(
    client: TestClient,
    admin_token: str,
    ngo_token: str,
    volunteer_token: str,
    citizen_token: str,
    relief_request_data,
):
    # 1. Citizen creates relief request (status: pending)
    cit_headers = {"Authorization": f"Bearer {citizen_token}"}
    create_res = client.post("/api/v1/relief-requests", json=relief_request_data, headers=cit_headers)
    assert create_res.status_code == 201
    mission_id = create_res.json()["id"]
    assert create_res.json()["status"] == "pending"

    # 2. Admin views mission list and detail
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    list_res = client.get("/api/v1/missions", headers=admin_headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    detail_res = client.get(f"/api/v1/missions/{mission_id}", headers=admin_headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["id"] == mission_id

    # 3. Transition: pending -> triaged
    triage_res = client.patch(
        f"/api/v1/missions/{mission_id}/status",
        json={"new_status": "triaged", "note": "Assessed by triage officer"},
        headers=admin_headers,
    )
    assert triage_res.status_code == 200
    assert triage_res.json()["status"] == "triaged"

    # 4. Transition: triaged -> assigned
    assigned_res = client.patch(
        f"/api/v1/missions/{mission_id}/status",
        json={"new_status": "assigned", "note": "Assigned to Red Cross Alpha unit"},
        headers=admin_headers,
    )
    assert assigned_res.status_code == 200
    assert assigned_res.json()["status"] == "assigned"

    # 5. Transition: assigned -> dispatched
    dispatch_res = client.patch(
        f"/api/v1/missions/{mission_id}/status",
        json={"new_status": "dispatched", "note": "Aid convoy departed depot"},
        headers=admin_headers,
    )
    assert dispatch_res.status_code == 200
    assert dispatch_res.json()["status"] == "dispatched"

    # 6. Transition: dispatched -> in_progress
    inprog_res = client.patch(
        f"/api/v1/missions/{mission_id}/status",
        json={"new_status": "in_progress", "note": "Arrived on ground"},
        headers=admin_headers,
    )
    assert inprog_res.status_code == 200
    assert inprog_res.json()["status"] == "in_progress"

    # 7. Transition: in_progress -> delivered
    deliv_res = client.patch(
        f"/api/v1/missions/{mission_id}/status",
        json={"new_status": "delivered", "note": "Supplies handed over to community head"},
        headers=admin_headers,
    )
    assert deliv_res.status_code == 200
    assert deliv_res.json()["status"] == "delivered"

    # 8. Transition: delivered -> completed
    comp_res = client.patch(
        f"/api/v1/missions/{mission_id}/status",
        json={"new_status": "completed", "note": "Mission finalized"},
        headers=admin_headers,
    )
    assert comp_res.status_code == 200
    assert comp_res.json()["status"] == "completed"

    # 9. Test Invalid Transition: completed -> in_progress (Must fail with 400)
    invalid_res = client.patch(
        f"/api/v1/missions/{mission_id}/status",
        json={"new_status": "in_progress", "note": "Attempt invalid revert"},
        headers=admin_headers,
    )
    assert invalid_res.status_code == 400

    # 10. Check mission history timeline
    hist_res = client.get(f"/api/v1/missions/{mission_id}/history", headers=admin_headers)
    assert hist_res.status_code == 200
    history = hist_res.json()
    assert len(history) >= 6
    assert history[-1]["new_status"] == "completed"
