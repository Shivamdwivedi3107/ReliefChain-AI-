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
def p14_env_data(db_session):
    org = Organization(
        name="Phase 14 Production Deployment NGO",
        registration_number="RC-P14-PROD",
        organization_type="International NGO",
        contact_email="deployment@reliefchain.ai",
        contact_phone="+1-800-555-0144",
        address="777 Production Boulevard",
        verification_status="verified",
        is_active=True,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    admin = User(
        email="admin_p14@reliefchain.ai",
        full_name="Phase 14 Incident Commander",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="admin",
        is_active=True,
        is_verified=True,
    )
    vol = User(
        email="vol_p14@reliefchain.ai",
        full_name="Phase 14 Elite Responder",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="volunteer",
        is_active=True,
        is_verified=True,
        skills=["medical", "water_purification", "search_rescue"],
        availability=True,
        max_mission_capacity=6,
        reliability_score=0.99,
        organization_id=org.id,
    )
    cit = User(
        email="citizen_p14@reliefchain.ai",
        full_name="Phase 14 Citizen Survivor",
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

    # Catalog resources
    res_water = Resource(
        name="P14 Potable Water (20L Cans)",
        category="water",
        unit="cans",
        description="Emergency drinking water cans",
    )
    db_session.add(res_water)
    db_session.commit()
    db_session.refresh(res_water)

    inv = ResourceInventory(
        organization_id=org.id,
        resource_id=res_water.id,
        total_quantity=2000.0,
        available_quantity=2000.0,
        reserved_quantity=0.0,
        warehouse_location="Primary Coastal Depot",
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


def test_phase14_production_settings_strict_guard():
    """Verify that production settings strictly enforce minimum 32-char secret and reject DEBUG=True."""
    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="valid-secret-key-32-chars-long-for-testing!!",
        )

    with pytest.raises(ValidationError):
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="too-short",
        )


def test_phase14_unified_crisis_response_e2e_flow(client, p14_env_data):
    """
    Test complete end-to-end lifecycle:
    1. Citizen creates relief request -> AI triage score generated.
    2. Admin creates disaster incident -> Status transition verified -> active.
    3. SPHERE shortage radar evaluates supply buffers.
    4. Cryptographic hash recorded on Merkle chain.
    5. AI Copilot summarizes operational readiness.
    """
    # 1. Citizen SOS Request
    cit_headers = {"Authorization": f"Bearer {p14_env_data['cit_token']}"}
    sos_payload = {
        "disaster_type": "flood",
        "location_name": "Bayfront Residential Sector 4",
        "latitude": 18.9220,
        "longitude": 72.8347,
        "affected_people": 25,
        "required_resources": ["water", "food", "medical"],
        "urgency_description": "Floodwaters reached first floor, multiple seniors requiring urgent medical and clean water",
    }
    resp_sos = client.post("/api/v1/relief-requests", json=sos_payload, headers=cit_headers)
    assert resp_sos.status_code == 201
    sos_data = resp_sos.json()
    assert sos_data["priority"] in ["critical", "high"]
    request_id = sos_data["id"]

    # 2. Admin Creates Incident and Activates Lifecycle
    admin_headers = {"Authorization": f"Bearer {p14_env_data['admin_token']}"}
    inc_payload = {
        "title": "Phase 14 Bayfront Monsoon Surge",
        "disaster_type": "flood",
        "severity": 8.5,
        "latitude": 18.9220,
        "longitude": 72.8347,
        "affected_radius_km": 25.0,
        "description": "Critical flash flood surge affecting coastal zones.",
    }
    resp_inc = client.post("/api/v1/incidents", json=inc_payload, headers=admin_headers)
    assert resp_inc.status_code == 201
    inc_data = resp_inc.json()
    assert inc_data["status"] == "DETECTED"
    inc_id = inc_data["id"]

    # Verify transition to VERIFIED then ACTIVE
    resp_v = client.post(f"/api/v1/incidents/{inc_id}/verify", headers=admin_headers)
    assert resp_v.status_code == 200
    assert resp_v.json()["status"] == "VERIFIED"

    resp_a = client.post(f"/api/v1/incidents/{inc_id}/activate", headers=admin_headers)
    assert resp_a.status_code == 200
    assert resp_a.json()["status"] == "ACTIVE"

    # 3. SPHERE Shortage Radar
    resp_radar = client.get("/api/v1/resources/shortage-radar", headers=admin_headers)
    assert resp_radar.status_code == 200
    radar_data = resp_radar.json()
    assert "categories" in radar_data
    assert "overall_threat_level" in radar_data

    # 4. Cryptographic Hash Chain Linkage
    h_block = blockchain_service.generate_sha256_hash(f"p14_delivery_receipt_{request_id}")
    tx_hash, blk, st = blockchain_service.record_hash_on_chain(
        record_hash=h_block,
        event_type="PROOF_OF_DELIVERY",
        reference_id=request_id,
    )
    assert tx_hash.startswith("0x")
    assert blk >= 1

    # 5. AI Copilot Operational Summary
    resp_copilot = client.post(
        "/api/v1/copilot/query",
        json={"prompt": "Summarize active critical emergencies"},
        headers=admin_headers,
    )
    assert resp_copilot.status_code == 200
    copilot_data = resp_copilot.json()
    assert "source" in copilot_data
    assert "ReliefChain AI" in copilot_data["source"]


def test_phase14_observability_and_request_id_tracing(client):
    """Verify Kubernetes health probes and correlation request ID injection."""
    # Liveness check
    resp_live = client.get("/health/live")
    assert resp_live.status_code == 200
    assert resp_live.json()["status"] == "alive"

    # Readiness check
    resp_ready = client.get("/health/ready")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["status"] == "ready"

    # Request ID Header
    resp_req = client.get("/health/live", headers={"X-Request-ID": "test-req-p14-trace-999"})
    assert resp_req.headers.get("x-request-id") == "test-req-p14-trace-999"


def test_phase14_pwa_runtime_and_display_overrides(client):
    """Verify PWA manifest parameters, categories, and shortcut configurations."""
    resp = client.get("/ui/manifest.json")
    assert resp.status_code == 200
    manifest = resp.json()
    assert manifest["short_name"] == "ReliefChain AI"
    assert manifest["display"] == "standalone"
    assert len(manifest["shortcuts"]) >= 3
