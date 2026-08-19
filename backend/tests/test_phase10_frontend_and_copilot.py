import pytest
from datetime import datetime, timezone

from app.models.user import User
from app.models.organization import Organization
from app.models.incidents import Incident, SituationReport
from app.models.relief_request import ReliefRequest
from app.models.resource import Resource, ResourceInventory
from app.models.donation import Donation
from app.models.distribution import Distribution
from app.models.blockchain import BlockchainTransaction
from app.core.security import create_access_token, get_password_hash


@pytest.fixture
def phase10_data(db_session):
    # Create test users
    admin_user = User(
        email="admin_p10@reliefchain.ai",
        full_name="Phase 10 Admin Commander",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="admin",
        is_active=True,
        is_verified=True,
    )
    db_session.add(admin_user)

    vol_user = User(
        email="vol_p10@reliefchain.ai",
        full_name="Phase 10 Field Responder",
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
        email="citizen_p10@reliefchain.ai",
        full_name="Phase 10 Citizen Resident",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="citizen",
        is_active=True,
        is_verified=True,
    )
    db_session.add(cit_user)

    # Create test incident
    inc = Incident(
        title="Phase 10 Verification Incident",
        disaster_type="flood",
        severity=8.5,
        status="ACTIVE",
        escalation_level="LEVEL_3_HIGH",
        latitude=22.5726,
        longitude=88.3639,
        affected_radius_km=35.0,
        description="High-tide coastal flash flood testing Phase 10 copilot and radar.",
    )
    db_session.add(inc)

    # Create test resources & inventory
    res = Resource(
        name="Potable Drinking Water (20L Cans)",
        category="water",
        unit="liters",
    )
    db_session.add(res)
    db_session.flush()

    # Create test blockchain transaction
    tx = BlockchainTransaction(
        event_type="DONATION_INGESTION",
        reference_id="test-ref-001",
        record_hash="0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        previous_hash="0x0000000000000000000000000000000000000000000000000000000000000000",
        tx_hash="0x7f8e1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        block_number=101,
        status="CONFIRMED",
    )
    db_session.add(tx)

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


def test_copilot_suggested_prompts(client):
    """Test retrieving recommended prompt chips for AI Disaster Copilot."""
    resp = client.get("/api/v1/copilot/suggested-prompts")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 3
    prompt_ids = [p["id"] for p in data]
    assert "critical_incidents" in prompt_ids
    assert "resource_shortages" in prompt_ids


def test_copilot_query_critical_incidents(client, phase10_data):
    """Test Copilot natural query for critical incidents."""
    headers = {"Authorization": f"Bearer {phase10_data['admin_token']}"}
    resp = client.post(
        "/api/v1/copilot/query",
        json={"prompt": "Show critical active disaster incidents"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["source"] == "ReliefChain AI Copilot (Operational Rule Engine)"
    assert "insights" in data
    assert "suggested_actions" in data
    assert len(data["suggested_actions"]) > 0


def test_copilot_query_resource_shortages(client, phase10_data):
    """Test Copilot natural query for supply and inventory shortage analysis."""
    headers = {"Authorization": f"Bearer {phase10_data['admin_token']}"}
    resp = client.post(
        "/api/v1/copilot/query",
        json={"prompt": "Find critical water and food shortage across depots"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert "SPHERE" in data["answer"] or "Demand" in data["answer"] or "Stock" in data["answer"]


def test_copilot_explain_incident(client, phase10_data):
    """Test Copilot reasoning diagnosis for a specific incident."""
    headers = {"Authorization": f"Bearer {phase10_data['admin_token']}"}
    resp = client.post(
        "/api/v1/copilot/query",
        json={"prompt": "Why is this incident classified with high severity?", "incident_id": phase10_data["incident_id"]},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["intent"] == "incident_explanation"
    assert phase10_data["incident_id"] in (data.get("incident_id") or "")


def test_resource_shortage_radar(client, phase10_data):
    """Test Resource Shortage Radar endpoint calculates coverage ratios and status codes."""
    resp = client.get("/api/v1/resources/shortage-radar?horizon_days=3")
    assert resp.status_code == 200
    data = resp.json()
    assert "overall_threat_level" in data
    assert data["overall_threat_level"] in ["GREEN", "YELLOW", "ORANGE", "RED"]
    assert "categories" in data
    assert len(data["categories"]) >= 5
    cat_names = [c["category"] for c in data["categories"]]
    assert "Water" in cat_names
    assert "Food" in cat_names


def test_transparency_journey_trace(client, phase10_data):
    """Test transparency journey tracing from donation to on-chain ledger."""
    resp = client.get("/api/v1/transparency/journey/test-ref-001")
    assert resp.status_code == 200
    data = resp.json()
    assert data["overall_status"] == "VERIFIED_ON_CHAIN"
    assert data["cryptographic_ledger_verified"] is True
    assert len(data["steps"]) >= 4
    step_phases = [s["phase"] for s in data["steps"]]
    assert "LEDGER_ENTRY" in step_phases
    assert "QR_VERIFICATION" in step_phases


def test_transparency_latest_journeys(client, phase10_data):
    """Test retrieving public recent transparency journeys."""
    resp = client.get("/api/v1/transparency/latest-journeys")
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)


def test_demo_scenarios_listing(client):
    """Test listing available pre-packaged demo scenarios."""
    resp = client.get("/api/v1/demo/scenarios")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) >= 3
    scenario_keys = [s["key"] for s in data]
    assert "flood_cyclone_crisis" in scenario_keys
    assert "seismic_emergency" in scenario_keys
    assert "wildfire_evacuation" in scenario_keys


def test_demo_scenario_load(client, phase10_data):
    """Test loading a demo crisis scenario into operational state."""
    headers = {"Authorization": f"Bearer {phase10_data['admin_token']}"}
    resp = client.post(
        "/api/v1/demo/scenarios/load",
        json={"scenario_key": "flood_cyclone_crisis"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["scenario_key"] == "flood_cyclone_crisis"
    assert data["sos_requests_created"] >= 1


def test_volunteer_smart_dashboard(client, phase10_data):
    """Test Volunteer smart dashboard endpoint with AI match scores and workload metrics."""
    headers = {"Authorization": f"Bearer {phase10_data['vol_token']}"}
    resp = client.get("/api/v1/dashboards/volunteer", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "volunteer" in data
    assert data["volunteer"]["full_name"] == "Phase 10 Field Responder"
    assert "workload_percentage" in data["volunteer"]
    assert "recommended_missions" in data


def test_citizen_smart_dashboard(client, phase10_data):
    """Test Citizen smart dashboard endpoint with safe locations and nearby incidents."""
    headers = {"Authorization": f"Bearer {phase10_data['cit_token']}"}
    resp = client.get("/api/v1/dashboards/citizen", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "my_requests" in data
    assert "nearby_incidents" in data
    assert "safe_locations" in data
    assert len(data["safe_locations"]) > 0


def test_citizen_quick_triage(client):
    """Test instant rule-based AI triage calculator for One-Tap SOS modal."""
    resp = client.post(
        "/api/v1/dashboards/citizen/quick-triage",
        json={
            "disaster_type": "flood",
            "severity": 8.0,
            "affected_people": 25,
            "requires_medical": True,
            "requires_water": True,
            "requires_food": False,
            "requires_shelter": False,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["priority_tier"] in ["High", "Critical"]
    assert "medical" in data["explanation"].lower()
    assert len(data["factors"]) >= 2


def test_system_health_summary(client):
    """Test System Health comprehensive technical monitoring endpoint."""
    resp = client.get("/api/v1/health/system-summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["system_status"] in ["HEALTHY", "DEGRADED"]
    assert "subsystems" in data
    assert "api_server" in data["subsystems"]
    assert "ai_engine" in data["subsystems"]
    assert "blockchain_ledger" in data["subsystems"]
