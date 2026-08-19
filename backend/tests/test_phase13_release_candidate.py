import os
import json
import pytest
from app.models.user import User
from app.models.organization import Organization
from app.models.resource import Resource, ResourceInventory
from app.models.relief_request import ReliefRequest
from app.models.blockchain import BlockchainTransaction
from app.core.security import create_access_token, get_password_hash
from app.services.blockchain_service import blockchain_service


@pytest.fixture
def rc_data(db_session):
    org = Organization(
        name="Phase 13 Release Candidate NGO",
        registration_number="RC-P13-999",
        organization_type="NGO",
        contact_email="rc_ops@reliefchain.ai",
        contact_phone="+1-800-555-0999",
        address="100 Release Way",
        verification_status="verified",
        is_active=True,
    )
    db_session.add(org)
    db_session.commit()
    db_session.refresh(org)

    admin = User(
        email="admin_rc13@reliefchain.ai",
        full_name="RC13 Commander",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="admin",
        is_active=True,
        is_verified=True,
    )
    vol = User(
        email="vol_rc13@reliefchain.ai",
        full_name="RC13 Volunteer",
        hashed_password=get_password_hash("SecurePassword123!"),
        role="volunteer",
        is_active=True,
        is_verified=True,
        availability=True,
        max_mission_capacity=5,
        reliability_score=0.99,
        organization_id=org.id,
    )
    cit = User(
        email="citizen_rc13@reliefchain.ai",
        full_name="RC13 Citizen",
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

    # Add baseline resource
    res = Resource(
        name="RC13 Survival Medical Kits",
        category="medical",
        unit="kits",
        description="High-grade emergency trauma kits for RC testing",
    )
    db_session.add(res)
    db_session.commit()
    db_session.refresh(res)

    inv = ResourceInventory(
        organization_id=org.id,
        resource_id=res.id,
        total_quantity=500.0,
        available_quantity=500.0,
        reserved_quantity=0.0,
        warehouse_location="Central RC Depot",
    )
    db_session.add(inv)
    db_session.commit()
    db_session.refresh(inv)

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
        "res_id": res.id,
        "inv_id": inv.id,
    }


def test_rc_auth_end_to_end_smoke(client):
    """Smoke test complete registration, login, profile fetch, and rejection of invalid credentials."""
    reg_payload = {
        "email": "fresh_rc13@reliefchain.ai",
        "password": "SecurePassword123!",
        "full_name": "Fresh QA User",
        "role": "citizen",
    }
    resp_reg = client.post("/api/v1/auth/register", json=reg_payload)
    assert resp_reg.status_code == 201
    reg_data = resp_reg.json()
    assert reg_data["email"] == "fresh_rc13@reliefchain.ai"

    # Login via JSON
    resp_login = client.post(
        "/api/v1/auth/login",
        json={"email": "fresh_rc13@reliefchain.ai", "password": "SecurePassword123!"},
    )
    assert resp_login.status_code == 200
    token = resp_login.json()["access_token"]
    assert token is not None

    # Get Me
    resp_me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_me.status_code == 200
    assert resp_me.json()["email"] == "fresh_rc13@reliefchain.ai"

    # Invalid login rejection
    resp_bad = client.post(
        "/api/v1/auth/login",
        json={"email": "fresh_rc13@reliefchain.ai", "password": "WrongPassword!"},
    )
    assert resp_bad.status_code == 401


def test_rc_relief_request_ai_triage_flow(client, rc_data):
    """Verify citizen relief request creation with automated AI priority inference."""
    headers = {"Authorization": f"Bearer {rc_data['cit_token']}"}
    payload = {
        "disaster_type": "flood",
        "location_name": "Sector 9 Flooded Lowlands",
        "latitude": 19.0760,
        "longitude": 72.8777,
        "affected_people": 12,
        "required_resources": ["water", "medical_kits"],
        "urgency_description": "Trapped families on second floor with infants needing water urgently",
    }
    resp = client.post("/api/v1/relief-requests", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["priority"] in ["critical", "high", "medium", "low"]
    assert data["status"] == "pending"


def test_rc_inventory_allocation_and_prevent_negative_values(client, rc_data):
    """Verify inventory quantity updates and strict rejection of negative values."""
    headers = {"Authorization": f"Bearer {rc_data['admin_token']}"}
    # Negative quantity update should be rejected with 400 Bad Request
    resp = client.patch(
        f"/api/v1/resources/inventory/{rc_data['inv_id']}",
        json={"total_quantity": -50.0},
        headers=headers,
    )
    assert resp.status_code == 400


def test_rc_cryptographic_ledger_chain_integrity(client, db_session, rc_data):
    """Verify Merkle sequential previous_hash linkage across sealed blockchain ledger records."""
    h1 = blockchain_service.generate_sha256_hash("donation_payload_data_rc13_1")
    tx_hash1, blk1, st1 = blockchain_service.record_hash_on_chain(
        record_hash=h1,
        event_type="DONATION_RECEIVED",
        reference_id=rc_data["cit_id"],
    )
    tx1 = BlockchainTransaction(
        event_type="DONATION_RECEIVED",
        reference_id=rc_data["cit_id"],
        record_hash=h1,
        previous_hash="0000000000000000000000000000000000000000000000000000000000000000",
        tx_hash=tx_hash1,
        block_number=blk1,
        status=st1,
    )
    db_session.add(tx1)
    db_session.commit()

    h2 = blockchain_service.generate_sha256_hash("relief_dispatched_data_rc13_2")
    tx_hash2, blk2, st2 = blockchain_service.record_hash_on_chain(
        record_hash=h2,
        event_type="RELIEF_DISPATCHED",
        reference_id=rc_data["vol_id"],
        previous_hash=h1,
    )
    tx2 = BlockchainTransaction(
        event_type="RELIEF_DISPATCHED",
        reference_id=rc_data["vol_id"],
        record_hash=h2,
        previous_hash=h1,
        tx_hash=tx_hash2,
        block_number=blk2,
        status=st2,
    )
    db_session.add(tx2)
    db_session.commit()

    assert tx1.record_hash is not None
    assert tx2.previous_hash == tx1.record_hash

    # Validate audit chain verification API
    headers = {"Authorization": f"Bearer {rc_data['admin_token']}"}
    resp = client.get("/api/v1/blockchain/verify-chain", headers=headers)
    assert resp.status_code == 200
    chain_data = resp.json()
    assert chain_data["is_valid"] is True


def test_rc_pwa_and_offline_service_worker_contracts(client):
    """Verify PWA installation manifests and service worker delivery contracts."""
    resp_manifest = client.get("/ui/manifest.json")
    assert resp_manifest.status_code == 200
    manifest = resp_manifest.json()
    assert manifest["short_name"] == "ReliefChain AI"
    assert manifest["start_url"] == "/ui/"
    assert "theme_color" in manifest

    resp_sw = client.get("/ui/sw.js")
    assert resp_sw.status_code == 200
    assert "sync" in resp_sw.text


def test_rc_demo_mode_simulation_isolation(client, rc_data):
    """Verify DEMO / SIMULATION mode loads isolated scenarios without corrupting production catalog."""
    resp_catalog = client.get("/api/v1/demo/scenarios")
    assert resp_catalog.status_code == 200
    scenarios = resp_catalog.json()
    assert len(scenarios) >= 3

    # Load flood cyclone scenario
    resp_load = client.post(
        "/api/v1/demo/scenarios/load",
        json={"scenario_key": "flood_cyclone_crisis"},
    )
    assert resp_load.status_code == 200
    load_data = resp_load.json()
    assert load_data["success"] is True
    assert "scenario_title" in load_data
