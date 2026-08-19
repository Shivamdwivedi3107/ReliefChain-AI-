import os
import io
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.services.geo_service import haversine_distance, geo_service
from app.services.recommendation_service import recommendation_engine
from app.services.simulation_service import simulation_engine
from app.services.notification_service import notification_manager
from app.services.metrics_service import MetricsCollector
from app.models.relief_request import ReliefRequest
from app.models.user import User
from app.models.notification import Notification
from app.models.evidence import Evidence


def test_haversine_distance_calculation():
    """Test Haversine distance between New Delhi and Agra (~180km)."""
    delhi_lat, delhi_lon = 28.6139, 77.2090
    agra_lat, agra_lon = 27.1767, 78.0081
    dist = haversine_distance(delhi_lat, delhi_lon, agra_lat, agra_lon)
    assert 170.0 <= dist <= 200.0


def test_haversine_same_point_is_zero():
    """Test distance between identical coordinates is 0.0 km."""
    assert haversine_distance(12.9716, 77.5946, 12.9716, 77.5946) == 0.0


def test_geo_nearby_requests_endpoint(client: TestClient, admin_token: str):
    """Test /geo/nearby-requests filtering."""
    # Create request 1 (Nearby Delhi)
    res1 = client.post(
        "/api/v1/relief-requests",
        json={
            "disaster_type": "flood",
            "location_name": "Yamuna Floodplain Sector 1",
            "latitude": 28.6200,
            "longitude": 77.2100,
            "affected_people": 10,
            "required_resources": [{"item": "water", "qty": 10}],
            "urgency_description": "Water level rising",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res1.status_code == 201

    # Create request 2 (Far away Mumbai)
    res2 = client.post(
        "/api/v1/relief-requests",
        json={
            "disaster_type": "cyclone",
            "location_name": "Marine Drive",
            "latitude": 18.9438,
            "longitude": 72.8232,
            "affected_people": 5,
            "required_resources": [{"item": "tents", "qty": 2}],
            "urgency_description": "High winds",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res2.status_code == 201

    # Search within 20km of Central Delhi
    response = client.get("/api/v1/geo/nearby-requests?latitude=28.6139&longitude=77.2090&radius_km=20")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["count"] >= 1
    names = [r["location_name"] for r in data["results"]]
    assert "Yamuna Floodplain Sector 1" in names


def test_geo_disaster_hotspots(client: TestClient, admin_token: str):
    """Test /geo/disaster-hotspots aggregation."""
    response = client.get("/api/v1/geo/disaster-hotspots")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "hotspots" in data


def test_volunteer_recommendation_scoring(client: TestClient, admin_token: str):
    """Test volunteer recommendation ranking for a disaster relief mission."""
    # 1. Create volunteer with medical skills
    reg_res = client.post(
        "/api/v1/auth/register",
        json={
            "email": "medic_vol@reliefchain.ai",
            "full_name": "Paramedic Priya",
            "password": "SecurePassword123!",
            "role": "volunteer",
            "phone_number": "+919888877777",
        },
    )
    assert reg_res.status_code == 201

    # 2. Create mission requiring trauma care
    req_res = client.post(
        "/api/v1/relief-requests",
        json={
            "disaster_type": "earthquake",
            "location_name": "Downtown Collapse Area",
            "latitude": 28.6139,
            "longitude": 77.2090,
            "affected_people": 25,
            "required_resources": [{"item": "trauma medical kits", "qty": 10}],
            "urgency_description": "Multiple casualties requiring emergency trauma surgical triage",
        },
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert req_res.status_code == 201
    mission_id = req_res.json()["id"]

    # 3. Get recommendations
    rec_res = client.get(
        f"/api/v1/missions/{mission_id}/recommended-volunteers",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert rec_res.status_code == 200
    data = rec_res.json()
    assert data["success"] is True
    assert "recommendations" in data
    assert "disclaimer" in data
    if data["recommendations"]:
        top_rec = data["recommendations"][0]
        assert "score" in top_rec
        assert "distance_km" in top_rec
        assert "skill_match" in top_rec


def test_recommendations_nonexistent_mission(client: TestClient, admin_token: str):
    """Test recommendations endpoint with a nonexistent mission returns 404."""
    res = client.get(
        "/api/v1/missions/nonexistent-mission-id/recommended-volunteers",
        headers={"Authorization": f"Bearer {admin_token}"},
    )
    assert res.status_code == 404


def test_notification_archive_and_filtering(client: TestClient, citizen_token: str):
    """Test notification archive, priority filtering, and unread counts."""
    # 1. Check unread count
    res_count = client.get("/api/v1/notifications/unread-count", headers={"Authorization": f"Bearer {citizen_token}"})
    assert res_count.status_code == 200
    assert "unread_count" in res_count.json()

    # 2. List notifications with category filter
    res_list = client.get(
        "/api/v1/notifications?category=SYSTEM&priority=MEDIUM",
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res_list.status_code == 200
    assert "notifications" in res_list.json()


def test_evidence_upload_and_security(client: TestClient, citizen_token: str):
    """Test uploading photographic proof of relief request."""
    # 1. Test invalid MIME type rejection
    bad_file = io.BytesIO(b"Fake executable or script payload")
    res_bad = client.post(
        "/api/v1/evidence/upload",
        files={"file": ("malicious.exe", bad_file, "application/x-msdownload")},
        data={"description": "Test bad file"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res_bad.status_code == 400

    # 2. Test valid PNG upload
    valid_png = io.BytesIO(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15c4")
    res_good = client.post(
        "/api/v1/evidence/upload",
        files={"file": ("disaster_site.png", valid_png, "image/png")},
        data={"description": "Photo of flooded bridge access"},
        headers={"Authorization": f"Bearer {citizen_token}"},
    )
    assert res_good.status_code == 201
    ev_data = res_good.json()["evidence"]
    assert ev_data["file_name"] == "disaster_site.png"
    assert ev_data["content_type"] == "image/png"
    evidence_id = ev_data["id"]

    # 3. Get metadata
    meta_res = client.get(f"/api/v1/evidence/{evidence_id}", headers={"Authorization": f"Bearer {citizen_token}"})
    assert meta_res.status_code == 200

    # 4. Delete evidence
    del_res = client.delete(f"/api/v1/evidence/{evidence_id}", headers={"Authorization": f"Bearer {citizen_token}"})
    assert del_res.status_code == 200


def test_ai_model_info_and_explainability(client: TestClient):
    """Test AI model info and Explainable AI (XAI) breakdown."""
    # 1. Model Info
    info_res = client.get("/api/v1/ai/model-info")
    assert info_res.status_code == 200
    info_data = info_res.json()
    assert info_data["success"] is True
    assert "RandomForest" in info_data["model_name"]
    assert "metrics" in info_data
    assert info_data["metrics"]["test_accuracy"] >= 0.85

    # 2. Explain Priority
    explain_res = client.post(
        "/api/v1/ai/explain-priority",
        json={
            "disaster_type": "flood",
            "affected_people": 45,
            "medical_needed": 1,
            "food_needed": 1,
            "water_needed": 1,
            "vulnerable_population": 1,
            "location_risk_score": 8.5,
        },
    )
    assert explain_res.status_code == 200
    explain_data = explain_res.json()
    assert explain_data["success"] is True
    assert explain_data["priority_score"] >= 70
    assert len(explain_data["factors"]) >= 2
    assert "dss_disclaimer" in explain_data


def test_disaster_simulation_lifecycle(client: TestClient, admin_token: str):
    """Test starting and stopping disaster drill simulation."""
    # 1. Get initial status
    status_1 = client.get("/api/v1/simulation/status")
    assert status_1.status_code == 200
    assert "is_running" in status_1.json()["simulation"]

    # 2. Start simulation
    start_res = client.post("/api/v1/simulation/start", json={"scenario": "cyclone_landing"})
    assert start_res.status_code == 200
    assert start_res.json()["simulation"]["is_running"] is True
    assert start_res.json()["simulation"]["injected_requests_count"] >= 1

    # 3. Stop simulation and purge
    stop_res = client.post("/api/v1/simulation/stop", json={"purge_data": True})
    assert stop_res.status_code == 200
    assert stop_res.json()["simulation"]["is_running"] is False


def test_metrics_prometheus_and_json(client: TestClient):
    """Test /metrics endpoint in Prometheus text and JSON modes."""
    # 1. Plain text Prometheus format
    prom_res = client.get("/metrics")
    assert prom_res.status_code == 200
    assert "reliefchain_http_requests_total" in prom_res.text
    assert "reliefchain_uptime_seconds" in prom_res.text

    # 2. JSON format via Accept header
    json_res = client.get("/metrics", headers={"Accept": "application/json"})
    assert json_res.status_code == 200
    data = json_res.json()
    assert "http_requests_total" in data
    assert "uptime_seconds" in data
    assert "database_entities" in data


def test_websocket_event_envelope_structure():
    """Verify standardized WebSocket event envelope format."""
    envelope = notification_manager.create_event_envelope(
        event_name="mission_status_changed",
        data={"mission_id": "req-123", "status": "dispatched"},
        req_id="test-correlation-uuid",
    )
    assert envelope["event"] == "mission_status_changed"
    assert envelope["request_id"] == "test-correlation-uuid"
    assert "timestamp" in envelope
    assert envelope["data"]["status"] == "dispatched"


def test_metrics_collector_recording():
    """Verify in-memory metrics recording logic."""
    mc = MetricsCollector()
    mc.record_request("/api/v1/requests", 200)
    mc.record_request("/api/v1/requests", 500)
    summary = mc.get_metrics_summary(db_stats={"relief_requests": 10}, active_ws_count=2)
    assert summary["http_requests_total"] == 2
    assert summary["http_errors_total"] == 1
    assert summary["active_websocket_connections"] == 2


def test_simulation_stop_without_purge(client: TestClient):
    """Test stopping simulation without purging synthetic data."""
    client.post("/api/v1/simulation/start", json={"scenario": "earthquake_swarm"})
    stop_res = client.post("/api/v1/simulation/stop", json={"purge_data": False})
    assert stop_res.status_code == 200
    assert stop_res.json()["simulation"]["purged_records_count"] == 0


def test_storage_provider_delete_nonexistent_returns_false():
    """Test storage provider handles nonexistent file deletion gracefully."""
    from app.services.storage_service import storage_provider
    res = storage_provider.delete_file("/nonexistent/file/path.png")
    assert res is False

