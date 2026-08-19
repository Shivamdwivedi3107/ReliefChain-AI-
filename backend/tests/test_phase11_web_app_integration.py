import os
import json
import pytest
from app.models.user import User
from app.models.incidents import Incident
from app.core.security import create_access_token, get_password_hash


@pytest.fixture
def phase11_data(db_session):
    admin_user = User(
        email="admin_p11@reliefchain.ai",
        full_name="Phase 11 Admin Commander",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin_user)

    vol_user = User(
        email="vol_p11@reliefchain.ai",
        full_name="Phase 11 Field Responder",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="volunteer",
        is_active=True,
        is_verified=True,
        skills=["medical", "first_aid", "search_rescue"],
        availability=True,
        max_mission_capacity=4,
        reliability_score=0.95,
    )
    db_session.add(vol_user)

    cit_user = User(
        email="citizen_p11@reliefchain.ai",
        full_name="Phase 11 Citizen Resident",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="citizen",
        is_active=True,
        is_verified=True,
    )
    db_session.add(cit_user)

    inc = Incident(
        title="Phase 11 Web App Verification Incident",
        disaster_type="flood",
        severity=8.5,
        status="ACTIVE",
        escalation_level="LEVEL_3_HIGH",
        latitude=22.5726,
        longitude=88.3639,
        affected_radius_km=35.0,
        description="Phase 11 verification incident for UI/UX integration.",
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


def test_frontend_static_mount_and_html_entrypoint(client):
    """Verify that FastAPI mounts and serves the web application shell at /ui/."""
    response = client.get("/ui/")
    assert response.status_code == 200
    assert "ReliefChain" in response.text
    assert "Persona" in response.text or "Citizen" in response.text


def test_frontend_manifest_and_sw_present(client):
    """Verify PWA manifest and service worker exist."""
    resp_manifest = client.get("/ui/manifest.json")
    assert resp_manifest.status_code == 200
    manifest_data = resp_manifest.json()
    assert "name" in manifest_data

    resp_sw = client.get("/ui/sw.js")
    assert resp_sw.status_code == 200


def test_frontend_typescript_structure_and_package_config():
    """Verify frontend/src structure, package.json, and tsconfig are valid."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    
    pkg_path = os.path.join(root_dir, "package.json")
    assert os.path.exists(pkg_path), "package.json missing"
    with open(pkg_path, "r", encoding="utf-8") as f:
        pkg = json.load(f)
    assert pkg["name"] == "reliefchain-ai-frontend"
    assert "react" in pkg["dependencies"]
    assert "vite" in pkg["devDependencies"]

    tsconfig_path = os.path.join(root_dir, "tsconfig.json")
    assert os.path.exists(tsconfig_path), "tsconfig.json missing"

    src_dir = os.path.join(root_dir, "src")
    assert os.path.exists(os.path.join(src_dir, "types", "index.ts"))
    assert os.path.exists(os.path.join(src_dir, "services", "api.ts"))
    assert os.path.exists(os.path.join(src_dir, "pages", "CitizenDashboard.tsx"))
    assert os.path.exists(os.path.join(src_dir, "pages", "VolunteerDashboard.tsx"))
    assert os.path.exists(os.path.join(src_dir, "pages", "AdminCommandCenter.tsx"))
    assert os.path.exists(os.path.join(src_dir, "pages", "AICopilotPage.tsx"))


def test_citizen_role_e2e_flow(client, phase11_data):
    """Verify citizen pre-flight triage and dashboard queries."""
    # 1. Quick Triage
    triage_resp = client.post(
        "/api/v1/dashboards/citizen/quick-triage",
        json={
            "disaster_type": "flood",
            "severity": 8.0,
            "affected_people": 10,
            "requires_medical": True,
            "requires_water": True,
            "requires_food": False,
            "requires_shelter": False,
        },
    )
    assert triage_resp.status_code == 200
    triage_data = triage_resp.json()
    assert triage_data["priority_tier"] in ["High", "Critical"]
    assert len(triage_data["factors"]) >= 2

    # 2. Citizen Dashboard query
    headers = {"Authorization": f"Bearer {phase11_data['cit_token']}"}
    dash_resp = client.get("/api/v1/dashboards/citizen", headers=headers)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert "safe_locations" in dash_data
    assert "my_requests" in dash_data


def test_volunteer_role_e2e_flow(client, phase11_data):
    """Verify volunteer workload metrics, recommendations, and capacity calculation."""
    headers = {"Authorization": f"Bearer {phase11_data['vol_token']}"}
    vol_resp = client.get("/api/v1/dashboards/volunteer", headers=headers)
    assert vol_resp.status_code == 200
    vol_data = vol_resp.json()
    assert "volunteer" in vol_data
    assert vol_data["volunteer"]["full_name"] == "Phase 11 Field Responder"
    assert "workload_percentage" in vol_data["volunteer"]
    assert "recommended_missions" in vol_data


def test_admin_command_center_and_health_flow(client, phase11_data):
    """Verify command center metrics and system health telemetry for admin role."""
    headers = {"Authorization": f"Bearer {phase11_data['admin_token']}"}
    cmd_resp = client.get("/api/v1/command-center/summary", headers=headers)
    assert cmd_resp.status_code == 200
    cmd_data = cmd_resp.json()
    assert "active_incidents_count" in cmd_data
    assert "system_readiness" in cmd_data

    health_resp = client.get("/api/v1/health/system-summary")
    assert health_resp.status_code == 200
    health_data = health_resp.json()
    assert health_data["system_status"] in ["HEALTHY", "DEGRADED"]
    assert "api_server" in health_data["subsystems"]
    assert "blockchain_ledger" in health_data["subsystems"]


def test_copilot_and_shortage_radar_contracts(client, phase11_data):
    """Verify AI Copilot queries and SPHERE Shortage Radar contracts."""
    # Copilot Suggested Prompts
    prompts_resp = client.get("/api/v1/copilot/suggested-prompts")
    assert prompts_resp.status_code == 200
    prompts = prompts_resp.json()
    assert isinstance(prompts, list)
    assert len(prompts) >= 3

    # Copilot Query
    headers = {"Authorization": f"Bearer {phase11_data['admin_token']}"}
    query_resp = client.post(
        "/api/v1/copilot/query",
        json={"prompt": "Find resource shortages", "incident_id": None},
        headers=headers,
    )
    assert query_resp.status_code == 200
    query_data = query_resp.json()
    assert "insights" in query_data or "answer" in query_data

    # Shortage Radar
    radar_resp = client.get("/api/v1/resources/shortage-radar?horizon_days=3")
    assert radar_resp.status_code == 200
    radar_data = radar_resp.json()
    assert "overall_threat_level" in radar_data
    assert len(radar_data["categories"]) >= 4


def test_demo_scenarios_and_transparency_journey(client, phase11_data):
    """Verify multi-hazard demo scenarios and transparency journey traces."""
    # Demo Scenarios
    scenarios_resp = client.get("/api/v1/demo/scenarios")
    assert scenarios_resp.status_code == 200
    scenarios = scenarios_resp.json()
    assert isinstance(scenarios, list)
    assert len(scenarios) >= 3

    # Transparency Latest Journeys
    journeys_resp = client.get("/api/v1/transparency/latest-journeys")
    assert journeys_resp.status_code == 200
    journeys = journeys_resp.json()
    assert isinstance(journeys, list)
