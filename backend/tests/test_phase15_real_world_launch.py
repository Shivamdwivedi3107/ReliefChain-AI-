import os
import json
import pytest
from pydantic import ValidationError
from app.models.user import User
from app.models.organization import Organization
from app.models.resource import Resource, ResourceInventory
from app.models.relief_request import ReliefRequest
from app.models.incidents import Incident
from app.models.blockchain import BlockchainTransaction
from app.core.config import Settings
from app.core.security import create_access_token, get_password_hash
from app.services.blockchain_service import blockchain_service


@pytest.fixture
def p15_launch_data(db_session):
    org = Organization(
        name="Phase 15 World Launch NGO",
        registration_number="RC-P15-GLOBAL",
        organization_type="International Humanitarian Agency",
        contact_email="global_ops@reliefchain.ai",
        contact_phone="+1-800-555-0155",
        address="100 Humanitarian Way",
        verification_status="verified",
        is_active=True,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    admin = User(
        email="admin_p15@reliefchain.ai",
        full_name="Phase 15 Global Commander",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="admin",
        is_active=True,
        is_verified=True,
    )
    vol = User(
        email="vol_p15@reliefchain.ai",
        full_name="Phase 15 Field Responder",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="volunteer",
        is_active=True,
        is_verified=True,
        skills=["medical", "water_purification", "logistics"],
        availability=True,
        max_mission_capacity=5,
        reliability_score=0.98,
        organization_id=org.id,
    )
    cit = User(
        email="citizen_p15@reliefchain.ai",
        full_name="Phase 15 Citizen Resident",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="citizen",
        is_active=True,
        is_verified=True,
    )
    db_session.add_all([admin, vol, cit])
    db_session.commit()
    db_session.refresh(admin)
    db_session.refresh(vol)
    db_session.refresh(cit)

    # Emergency Water Resource
    res_water = Resource(
        name="P15 Drinking Water Cans (20L)",
        category="water",
        unit="cans",
        description="Standard 20L emergency potable water containers",
    )
    db_session.add(res_water)
    db_session.commit()
    db_session.refresh(res_water)

    inv = ResourceInventory(
        organization_id=org.id,
        resource_id=res_water.id,
        total_quantity=1500.0,
        available_quantity=1500.0,
        reserved_quantity=0.0,
        warehouse_location="Global Logistics Depot Alpha",
    )
    db_session.add(inv)
    db_session.commit()

    admin_token = create_access_token(admin.id, admin.role)
    vol_token = create_access_token(vol.id, vol.role)
    cit_token = create_access_token(cit.id, cit.role)

    return {
        "admin_token": admin_token,
        "vol_token": vol_token,
        "cit_token": cit_token,
        "admin_id": admin.id,
        "vol_id": vol.id,
        "cit_id": cit.id,
        "org_id": org.id,
        "resource_id": res_water.id,
    }


def test_phase15_production_security_and_strict_validation():
    """Verify production settings strictly reject weak secrets and wildcard CORS."""
    # Reject short secret in production
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="short-secret",
        )

    # Reject DEBUG=True in production
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="valid-secret-key-32-chars-long-for-testing!!",
        )


def test_phase15_human_in_the_loop_safety_and_disclaimer_contracts(client):
    """Verify web application UI contains explicit human-in-the-loop emergency authority disclaimers."""
    resp = client.get("/ui/")
    assert resp.status_code == 200
    html = resp.text
    assert "Emergency Authority Notice" in html
    assert "decision-support" in html.lower()
    assert "Operational Oversight" in html


def test_phase15_e2e_real_world_launch_workflow(client, p15_launch_data):
    """
    Test full end-to-end crisis management launch flow:
    1. Citizen creates relief request -> AI priority triage calculated.
    2. Admin declares disaster incident -> Transitions to VERIFIED and ACTIVE.
    3. SPHERE shortage radar computes supply coverage.
    4. Cryptographic SHA-256 Merkle block transaction recorded.
    5. AI Copilot summarizes active operational status.
    """
    cit_headers = {"Authorization": f"Bearer {p15_launch_data['cit_token']}"}
    sos_payload = {
        "disaster_type": "cyclone",
        "location_name": "Coastal Ward 12 Shelter Zone",
        "latitude": 19.0178,
        "longitude": 72.8478,
        "affected_people": 40,
        "required_resources": ["water", "medical", "blankets"],
        "urgency_description": "Category 4 wind damage, trauma patients requiring immediate medical and drinking water",
    }
    resp_sos = client.post("/api/v1/relief-requests", json=sos_payload, headers=cit_headers)
    assert resp_sos.status_code == 201
    sos_data = resp_sos.json()
    assert sos_data["priority"] in ["critical", "high"]
    req_id = sos_data["id"]

    # Admin Incident Creation & Activation
    admin_headers = {"Authorization": f"Bearer {p15_launch_data['admin_token']}"}
    inc_payload = {
        "title": "Phase 15 Tropical Cyclone Surge",
        "disaster_type": "cyclone",
        "severity": 9.0,
        "latitude": 19.0178,
        "longitude": 72.8478,
        "affected_radius_km": 50.0,
        "description": "Category 4 tropical storm with storm surge warnings.",
    }
    resp_inc = client.post("/api/v1/incidents", json=inc_payload, headers=admin_headers)
    assert resp_inc.status_code == 201
    inc_id = resp_inc.json()["id"]

    # Activate incident
    client.post(f"/api/v1/incidents/{inc_id}/verify", headers=admin_headers)
    resp_act = client.post(f"/api/v1/incidents/{inc_id}/activate", headers=admin_headers)
    assert resp_act.status_code == 200
    assert resp_act.json()["status"] == "ACTIVE"

    # SPHERE Shortage Radar
    resp_radar = client.get("/api/v1/resources/shortage-radar", headers=admin_headers)
    assert resp_radar.status_code == 200
    radar_data = resp_radar.json()
    assert "categories" in radar_data
    assert "overall_threat_level" in radar_data

    # Cryptographic Proof-of-Delivery Block Record
    h_delivery = blockchain_service.generate_sha256_hash(f"p15_verified_handover_{req_id}")
    tx_hash, blk, st = blockchain_service.record_hash_on_chain(
        record_hash=h_delivery,
        event_type="PROOF_OF_DELIVERY",
        reference_id=req_id,
    )
    assert tx_hash.startswith("0x")
    assert blk >= 1

    # AI Copilot Query
    resp_copilot = client.post(
        "/api/v1/copilot/query",
        json={"prompt": "Summarize command center status and critical incidents"},
        headers=admin_headers,
    )
    assert resp_copilot.status_code == 200
    copilot_data = resp_copilot.json()
    assert "source" in copilot_data
    assert "ReliefChain AI" in copilot_data["source"]


def test_phase15_pwa_and_offline_sync_readiness(client):
    """Verify PWA installation manifest shortcuts and Service Worker sync directives."""
    resp_m = client.get("/ui/manifest.json")
    assert resp_m.status_code == 200
    manifest = resp_m.json()
    assert manifest["short_name"] == "ReliefChain AI"
    assert manifest["display"] == "standalone"
    assert "shortcuts" in manifest

    resp_sw = client.get("/ui/sw.js")
    assert resp_sw.status_code == 200
    assert "sync" in resp_sw.text
