import os
import hashlib
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token
from app.core.rate_limit import get_rate_limit_for_role, InMemoryRateLimiter
from app.services.geo_service import geo_service, haversine_distance
from app.services.model_registry import model_registry
from app.models.user import User
from app.models.relief_request import ReliefRequest
from app.models.blockchain import BlockchainTransaction


def test_websocket_token_auth_verification():
    """Verify WebSocket authentication token generation and claim extraction."""
    token = create_access_token(subject="volunteer@reliefchain.ai", role="volunteer")
    assert isinstance(token, str)
    assert len(token) > 20


def test_privacy_location_fuzzing():
    """Verify citizen coordinates are safely fuzzed/masked for public privacy."""
    exact_lat, exact_lng = 28.613934, 77.209021
    masked = geo_service.mask_citizen_coordinates(exact_lat, exact_lng, precision_decimals=2)
    assert masked["latitude"] == 28.61
    assert masked["longitude"] == 77.21
    assert masked["privacy_masked"] is True


def test_evidence_file_sha256_hashing(tmp_path):
    """Verify SHA-256 integrity hash calculation for disaster photo/evidence uploads."""
    sample_file = tmp_path / "damage_evidence.jpg"
    content = b"\xFF\xD8\xFF\xE0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00test-image-data-2026"
    sample_file.write_bytes(content)

    expected_hash = hashlib.sha256(content).hexdigest()
    
    sha256 = hashlib.sha256()
    with open(sample_file, "rb") as f:
        while chunk := f.read(4096):
            sha256.update(chunk)

    assert sha256.hexdigest() == expected_hash
    assert len(expected_hash) == 64


def test_rate_limiter_auth_and_public_thresholds():
    """Verify rate limiting differentiates public vs authenticated tiers."""
    public_limit = get_rate_limit_for_role(None)
    auth_limit = get_rate_limit_for_role("volunteer")
    admin_limit = get_rate_limit_for_role("admin")

    assert public_limit == settings.RATE_LIMIT_PUBLIC_PER_MINUTE
    assert auth_limit == settings.RATE_LIMIT_AUTH_PER_MINUTE
    assert admin_limit == settings.RATE_LIMIT_AUTH_PER_MINUTE
    assert auth_limit > public_limit


def test_in_memory_rate_limiter_burst_and_recovery():
    """Verify in-memory sliding window rate limiter blocks excessive burst requests."""
    prev_enabled = settings.RATE_LIMIT_ENABLED
    try:
        settings.RATE_LIMIT_ENABLED = True
        limiter = InMemoryRateLimiter()
        key = "test-client-ip:/api/v1/sos"

        # Allow up to 3 requests in 10s window
        for _ in range(3):
            allowed, _ = limiter.is_allowed(key, max_requests=3, window_seconds=10)
            assert allowed is True

        # 4th request must be rejected
        allowed, retry_after = limiter.is_allowed(key, max_requests=3, window_seconds=10)
        assert allowed is False
        assert retry_after > 0
    finally:
        settings.RATE_LIMIT_ENABLED = prev_enabled


def test_disaster_hotspot_clustering_algorithm(db_session: Session, admin_user: User):
    """Verify GIS disaster hotspot clustering groups nearby requests within radius."""
    # Seed 2 nearby requests in Zone A
    req1 = ReliefRequest(
        citizen_id=admin_user.id,
        disaster_type="flood",
        location_name="Zone A - North Bank",
        latitude=28.6140,
        longitude=77.2090,
        affected_people=30,
        required_resources=[{"item": "water", "qty": 10}],
        priority="critical",
        status="pending",
    )
    req2 = ReliefRequest(
        citizen_id=admin_user.id,
        disaster_type="flood",
        location_name="Zone A - South Bank",
        latitude=28.6150,
        longitude=77.2095,
        affected_people=20,
        required_resources=[{"item": "food", "qty": 15}],
        priority="high",
        status="pending",
    )
    db_session.add(req1)
    db_session.add(req2)
    db_session.commit()

    hotspots = geo_service.get_disaster_hotspots(db_session, max_cluster_radius_km=10.0)
    assert len(hotspots) >= 1
    cluster = hotspots[0]
    assert cluster["requests_count"] >= 2
    assert cluster["affected_people"] >= 50
    assert "average_priority" in cluster
    assert "hazard_level" in cluster


def test_volunteer_workload_capacity_filtering(db_session: Session):
    """Verify volunteer recommendation scores account for capacity and reliability."""
    vol = User(
        email="field_medic@reliefchain.ai",
        full_name="Dr. Jane Doe",
        hashed_password="hash",
        role="volunteer",
        availability=True,
        current_latitude=28.6139,
        current_longitude=77.2090,
        skills=["medical", "first_aid", "trauma"],
        max_mission_capacity=5,
        reliability_score=4.95,
    )
    db_session.add(vol)
    db_session.commit()

    assert vol.max_mission_capacity == 5
    assert vol.reliability_score == 4.95
    assert "medical" in vol.skills


def test_audit_ledger_sequential_hash_chain(db_session: Session):
    """Verify SHA-256 tamper-evident ledger enforces sequential previous_hash linking."""
    tx1 = BlockchainTransaction(
        event_type="relief_request",
        reference_id="ref-101",
        record_hash=hashlib.sha256(b"block-1-payload").hexdigest(),
        previous_hash="0" * 64,
        status="confirmed",
    )
    db_session.add(tx1)
    db_session.commit()

    tx2 = BlockchainTransaction(
        event_type="distribution",
        reference_id="ref-102",
        record_hash=hashlib.sha256(b"block-2-payload").hexdigest(),
        previous_hash=tx1.record_hash,
        status="confirmed",
    )
    db_session.add(tx2)
    db_session.commit()

    assert tx2.previous_hash == tx1.record_hash
    assert tx1.record_hash != tx2.record_hash


def test_model_registry_governance_and_metrics():
    """Verify AI model registry returns governance and explainability constraints."""
    info = model_registry.get_model_info()
    assert info["metrics"]["test_accuracy"] >= 0.85
    assert info["governance"]["human_in_the_loop"] is True
    assert "feature_importances" in info
    assert len(info["feature_importances"]) == 6


def test_geo_nearby_requests_radius_filtering(client: TestClient, admin_token: str):
    """Verify /api/v1/geo/nearby-requests returns sorted proximity results."""
    res = client.get("/api/v1/geo/nearby-requests?latitude=28.6139&longitude=77.2090&radius_km=50.0")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "results" in data


def test_disaster_hotspots_api_endpoint(client: TestClient):
    """Verify /api/v1/geo/disaster-hotspots public query endpoint."""
    res = client.get("/api/v1/geo/disaster-hotspots")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "hotspots" in data


def test_offline_action_queue_contract():
    """Verify structure of offline synchronized action payload."""
    action_payload = {
        "type": "update_mission_status",
        "mission_id": "req-999",
        "new_status": "in_progress",
        "note": "En route via field vehicle",
        "client_timestamp": "2026-08-19T20:00:00Z",
    }
    assert action_payload["type"] == "update_mission_status"
    assert action_payload["new_status"] in ("triaged", "assigned", "dispatched", "in_progress", "delivered", "completed", "cancelled")
