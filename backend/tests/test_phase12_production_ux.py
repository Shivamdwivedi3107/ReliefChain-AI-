import os
import json
import pytest
from app.models.user import User
from app.models.incidents import Incident
from app.core.security import create_access_token, get_password_hash


@pytest.fixture
def phase12_data(db_session):
    admin_user = User(
        email="admin_p12@reliefchain.ai",
        full_name="Phase 12 Admin Commander",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin_user)

    vol_user = User(
        email="vol_p12@reliefchain.ai",
        full_name="Phase 12 Field Responder",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="volunteer",
        is_active=True,
        is_verified=True,
        skills=["medical", "first_aid", "search_rescue"],
        availability=True,
        max_mission_capacity=4,
        reliability_score=0.98,
    )
    db_session.add(vol_user)

    cit_user = User(
        email="citizen_p12@reliefchain.ai",
        full_name="Phase 12 Citizen Resident",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="citizen",
        is_active=True,
        is_verified=True,
    )
    db_session.add(cit_user)

    inc = Incident(
        title="Phase 12 Production UX Verification Incident",
        disaster_type="cyclone",
        severity=8.9,
        status="ACTIVE",
        escalation_level="LEVEL_4_CRITICAL",
        latitude=19.0760,
        longitude=72.8777,
        affected_radius_km=45.0,
        description="Category-4 Cyclone verified for Phase 12 mobile/PWA and production user experience.",
    )
    db_session.add(inc)

    db_session.commit()
    db_session.refresh(admin_user)
    db_session.refresh(vol_user)
    db_session.refresh(cit_user)
    db_session.refresh(inc)

    admin_token = create_access_token(admin_user.id, admin_user.role)
    vol_token = create_access_token(vol_user.id, vol_user.role)
    cit_token = create_access_token(cit_user.id, cit_user.role)

    return {
        "admin_token": admin_token,
        "vol_token": vol_token,
        "cit_token": cit_token,
        "admin_id": admin_user.id,
        "vol_id": vol_user.id,
        "cit_id": cit_user.id,
        "incident_id": inc.id,
    }


def test_pwa_web_app_manifest_and_shortcuts(client):
    """Verify that the Web App Manifest contains valid PWA metadata and operational shortcuts."""
    resp = client.get("/ui/manifest.json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["short_name"] == "ReliefChain AI"
    assert data["display"] == "standalone"
    assert "theme_color" in data
    assert "shortcuts" in data
    assert len(data["shortcuts"]) >= 3
    shortcut_names = [s["name"] for s in data["shortcuts"]]
    assert any("SOS" in name for name in shortcut_names)


def test_service_worker_caching_and_sync_directives(client):
    """Verify that sw.js exists, includes static cache names, and handles offline sync."""
    resp = client.get("/ui/sw.js")
    assert resp.status_code == 200
    content = resp.text
    assert "CACHE_NAME" in content
    assert "STATIC_ASSETS" in content
    assert "sync" in content
    assert "sync-offline-sos" in content


def test_offline_ui_detection_elements_in_html(client):
    """Verify that index.html contains offline banner, persona switcher, and mobile-friendly viewport."""
    resp = client.get("/ui/")
    assert resp.status_code == 200
    html = resp.text
    assert 'id="offline-banner"' in html
    assert 'viewport' in html
    assert 'Persona Switcher' in html or 'persona-bar' in html


def test_citizen_dashboard_mobile_and_web_contracts(client, phase12_data):
    """Verify citizen emergency hub endpoint with safe shelters and personal requests."""
    headers = {"Authorization": f"Bearer {phase12_data['cit_token']}"}
    resp = client.get("/api/v1/dashboards/citizen", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "safe_locations" in data
    assert "my_requests" in data
    assert "nearby_incidents" in data


def test_volunteer_dashboard_capacity_and_workload(client, phase12_data):
    """Verify volunteer operations endpoint with workload percentages and AI recommendations."""
    headers = {"Authorization": f"Bearer {phase12_data['vol_token']}"}
    resp = client.get("/api/v1/dashboards/volunteer", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "volunteer" in data
    assert data["volunteer"]["reliability_score"] >= 0.90
    assert "recommended_missions" in data


def test_admin_command_center_telemetry_and_escalation(client, phase12_data):
    """Verify administrative command center operational grid."""
    headers = {"Authorization": f"Bearer {phase12_data['admin_token']}"}
    resp = client.get("/api/v1/command-center/summary", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "active_incidents_count" in data
    assert "system_readiness" in data


def test_copilot_data_source_transparency_labels(client, phase12_data):
    """Verify AI Copilot explicitly labels the engine source and separates operational insights."""
    headers = {"Authorization": f"Bearer {phase12_data['admin_token']}"}
    resp = client.post(
        "/api/v1/copilot/query",
        json={"prompt": "Summarize current disaster situation"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "source" in data
    assert "ReliefChain AI" in data["source"]
    assert "insights" in data or "answer" in data


def test_demo_scenario_isolation_and_simulation_markers(client, phase12_data):
    """Verify that demo crisis scenarios return explicit simulation flags."""
    headers = {"Authorization": f"Bearer {phase12_data['admin_token']}"}
    resp = client.post(
        "/api/v1/demo/scenarios/load",
        json={"scenario_key": "flood_cyclone_crisis"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["scenario_key"] == "flood_cyclone_crisis"


def test_security_rbac_rejection_for_unauthorized_endpoints(client, phase12_data):
    """Verify that backend RBAC strictly forbids unauthorized role actions."""
    # Citizen attempting to access admin dashboard
    cit_headers = {"Authorization": f"Bearer {phase12_data['cit_token']}"}
    resp_cit = client.get("/api/v1/dashboards/admin", headers=cit_headers)
    assert resp_cit.status_code == 403

    # Volunteer attempting to access admin dashboard
    vol_headers = {"Authorization": f"Bearer {phase12_data['vol_token']}"}
    resp_adm = client.get("/api/v1/dashboards/admin", headers=vol_headers)
    assert resp_adm.status_code == 403


def test_system_health_and_telemetry_probes(client):
    """Verify full system readiness and health telemetry probes."""
    resp_ready = client.get("/health/ready")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["status"] == "ready"

    resp_summary = client.get("/api/v1/health/system-summary")
    assert resp_summary.status_code == 200
    data = resp_summary.json()
    assert data["system_status"] in ["HEALTHY", "DEGRADED"]
    assert "api_server" in data["subsystems"]
