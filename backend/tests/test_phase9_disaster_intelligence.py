import asyncio
import pytest
from datetime import datetime, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.organization import Organization
from app.models.incidents import DisasterEvent, Incident, IncidentTimeline, SituationReport
from app.models.relief_request import ReliefRequest
from app.core.security import create_access_token, get_password_hash
from app.services.disaster_intelligence import (
    MockDisasterProvider,
    normalize_event_payload,
    provider_registry,
)
from app.services.incident_service import incident_service
from app.services.escalation_service import escalation_service
from app.services.disaster_intelligence_sync import disaster_sync_service

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def auth_headers_admin(db_session: Session):
    admin = db_session.query(User).filter(User.email == "phase9_admin@reliefchain.ai").first()
    if not admin:
        admin = User(
            email="phase9_admin@reliefchain.ai",
            hashed_password=get_password_hash("AdminPass123!"),
            full_name="Phase 9 Operations Admin",
            role="admin",
            is_active=True,
        )
        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)
    token = create_access_token(admin.id, "admin")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_ngo(db_session: Session):
    org = db_session.query(Organization).filter(Organization.name == "Phase 9 Red Cross").first()
    if not org:
        org = Organization(
            name="Phase 9 Red Cross",
            registration_number="REG-RC-P9-001",
            organization_type="NGO",
            contact_email="contact_p9@redcross.org",
            contact_phone="+1-800-RED-CROSS",
            address="77 Relief Ave, Capital City",
        )
        db_session.add(org)
        db_session.commit()
        db_session.refresh(org)

    ngo_user = db_session.query(User).filter(User.email == "phase9_ngo@reliefchain.ai").first()
    if not ngo_user:
        ngo_user = User(
            email="phase9_ngo@reliefchain.ai",
            hashed_password=get_password_hash("NgoPass123!"),
            full_name="Phase 9 NGO Commander",
            role="ngo",
            organization_id=org.id,
            is_active=True,
        )
        db_session.add(ngo_user)
        db_session.commit()
        db_session.refresh(ngo_user)
    token = create_access_token(ngo_user.id, "ngo")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_volunteer(db_session: Session):
    vol = db_session.query(User).filter(User.email == "phase9_volunteer@reliefchain.ai").first()
    if not vol:
        vol = User(
            email="phase9_volunteer@reliefchain.ai",
            hashed_password=get_password_hash("VolPass123!"),
            full_name="Phase 9 Field Volunteer",
            role="volunteer",
            is_active=True,
        )
        db_session.add(vol)
        db_session.commit()
        db_session.refresh(vol)
    token = create_access_token(vol.id, "volunteer")
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_citizen(db_session: Session):
    cit = db_session.query(User).filter(User.email == "phase9_citizen@reliefchain.ai").first()
    if not cit:
        cit = User(
            email="phase9_citizen@reliefchain.ai",
            hashed_password=get_password_hash("CitizenPass123!"),
            full_name="Phase 9 Citizen Reporter",
            role="citizen",
            is_active=True,
        )
        db_session.add(cit)
        db_session.commit()
        db_session.refresh(cit)
    token = create_access_token(cit.id, "citizen")
    return {"Authorization": f"Bearer {token}"}


# ---------------------------------------------------------------------------
# Unit & Service Tests
# ---------------------------------------------------------------------------

def test_disaster_event_normalization():
    """1. Test disaster event normalization handles diverse inputs safely."""
    raw = {
        "source": "custom_radar",
        "external_id": "RAD-001",
        "disaster_type": "CYCLONE",
        "severity": 12.5,  # Exceeds max, should clamp to 10.0
        "latitude": 195.0,  # Invalid latitude, should clamp to 90.0
        "longitude": 77.2,
        "affected_radius_km": 600.0,  # Exceeds max, clamps to 500.0
        "started_at": "2026-08-19T10:00:00Z",
        "confidence_score": 0.95,
        "raw_metadata": {"wind_speed": 180},
    }
    normalized = normalize_event_payload(raw)
    assert normalized.source == "custom_radar"
    assert normalized.disaster_type == "cyclone"
    assert normalized.severity == 10.0
    assert normalized.latitude == 90.0
    assert normalized.affected_radius_km == 500.0
    assert normalized.confidence_score == 0.95

    # Test unknown disaster type defaults to 'other'
    raw_unknown = {"disaster_type": "meteor_strike"}
    norm_unknown = normalize_event_payload(raw_unknown)
    assert norm_unknown.disaster_type == "other"
    assert norm_unknown.severity == 5.0


def test_mock_provider_event_retrieval():
    """2. Test mock provider returns multi-hazard events deterministically."""
    provider = MockDisasterProvider()
    assert provider.provider_name == "mock_provider"
    events = asyncio.run(provider.fetch_events())
    assert len(events) >= 6
    types = {e.disaster_type for e in events}
    assert "earthquake" in types
    assert "flood" in types
    assert "cyclone" in types
    assert "wildfire" in types


def test_duplicate_detection_and_disaster_sync(db_session: Session):
    """3. Test disaster feed synchronization, duplicate avoidance, and auto-incident provisioning."""
    # First sync run
    result1 = asyncio.run(
        disaster_sync_service.sync_provider(
            db=db_session,
            provider_name="mock_provider",
            auto_create_incidents=True,
        )
    )
    assert result1["success"] is True
    assert result1["new_events"] >= 6
    assert result1["incidents_created"] >= 6

    # Second sync run should detect duplicates and update rather than duplicate
    result2 = asyncio.run(
        disaster_sync_service.sync_provider(
            db=db_session,
            provider_name="mock_provider",
            auto_create_incidents=True,
        )
    )
    assert result2["success"] is True
    assert result2["new_events"] == 0
    assert result2["updated_events"] >= 6
    assert result2["incidents_created"] == 0


def test_incident_creation_and_timeline_entry(db_session: Session):
    """4. Test creating incident creates an initial INCIDENT_DETECTED timeline entry."""
    inc = incident_service.create_incident(
        db=db_session,
        title="Test Flood Inundation Area 7",
        disaster_type="flood",
        severity=7.2,
        latitude=28.6139,
        longitude=77.2090,
        affected_radius_km=15.0,
    )
    assert inc.id is not None
    assert inc.status == "DETECTED"

    timeline = (
        db_session.query(IncidentTimeline)
        .filter(IncidentTimeline.incident_id == inc.id)
        .all()
    )
    assert len(timeline) >= 1
    assert timeline[0].event_type == "INCIDENT_DETECTED"
    assert "7.2" in timeline[0].message


def test_incident_lifecycle_valid_transitions(db_session: Session):
    """5. Test full valid lifecycle transition path."""
    inc = incident_service.create_incident(
        db=db_session,
        title="Lifecycle Test Cyclone",
        disaster_type="cyclone",
        severity=8.0,
        latitude=13.0827,
        longitude=80.2707,
    )

    # DETECTED -> VERIFIED
    incident_service.transition_status(db_session, inc, "VERIFIED", note="Verified by field satellite")
    assert inc.status == "VERIFIED"

    # VERIFIED -> ACTIVE
    incident_service.transition_status(db_session, inc, "ACTIVE", note="Mobilizing response units")
    assert inc.status == "ACTIVE"

    # ACTIVE -> MONITORING
    incident_service.transition_status(db_session, inc, "MONITORING")
    assert inc.status == "MONITORING"

    # MONITORING -> CONTAINED
    incident_service.transition_status(db_session, inc, "CONTAINED")
    assert inc.status == "CONTAINED"

    # CONTAINED -> RESOLVED
    incident_service.transition_status(db_session, inc, "RESOLVED", note="Relief missions completed")
    assert inc.status == "RESOLVED"


def test_incident_lifecycle_invalid_transitions(db_session: Session):
    """6. Test invalid lifecycle transitions trigger HTTP 400."""
    from fastapi import HTTPException

    inc = incident_service.create_incident(
        db=db_session,
        title="Invalid Transition Test",
        disaster_type="earthquake",
        severity=6.0,
        latitude=28.0,
        longitude=77.0,
    )
    assert inc.status == "DETECTED"

    # Invalid: DETECTED cannot jump directly to RESOLVED
    with pytest.raises(HTTPException) as exc_info:
        incident_service.transition_status(db_session, inc, "RESOLVED")
    assert exc_info.value.status_code == 400
    assert "Invalid incident lifecycle transition" in exc_info.value.detail


# ---------------------------------------------------------------------------
# API Route & RBAC Tests
# ---------------------------------------------------------------------------

def test_incident_creation_and_rbac(auth_headers_ngo, auth_headers_citizen):
    """7 & 8. Test incident creation API and RBAC constraints."""
    payload = {
        "title": "API Created Coastal Storm Incident",
        "disaster_type": "storm",
        "severity": 6.8,
        "latitude": 19.0760,
        "longitude": 72.8777,
        "affected_radius_km": 25.0,
        "description": "High velocity coastal winds and squalls.",
    }

    # NGO can create
    res_ngo = client.post("/api/v1/incidents", json=payload, headers=auth_headers_ngo)
    assert res_ngo.status_code == 201
    data = res_ngo.json()
    assert data["title"] == payload["title"]
    assert data["status"] == "DETECTED"
    incident_id = data["id"]

    # Citizen cannot create
    res_cit = client.post("/api/v1/incidents", json=payload, headers=auth_headers_citizen)
    assert res_cit.status_code == 403

    # Public list incidents
    res_list = client.get("/api/v1/incidents")
    assert res_list.status_code == 200
    assert any(i["id"] == incident_id for i in res_list.json())


def test_incident_timeline_chronological_ordering(auth_headers_ngo, db_session: Session):
    """9 & 10. Test incident timeline endpoints and chronological sorting."""
    inc = incident_service.create_incident(
        db=db_session,
        title="Timeline Ordering Test",
        disaster_type="flood",
        severity=7.0,
        latitude=28.6,
        longitude=77.2,
    )

    # Verify and activate to generate timeline items
    incident_service.transition_status(db_session, inc, "VERIFIED", note="First step")
    incident_service.transition_status(db_session, inc, "ACTIVE", note="Second step")

    res = client.get(f"/api/v1/incidents/{inc.id}/timeline")
    assert res.status_code == 200
    timeline = res.json()
    assert len(timeline) >= 3
    assert timeline[0]["event_type"] == "INCIDENT_DETECTED"
    assert timeline[1]["event_type"] == "INCIDENT_VERIFIED"
    assert timeline[2]["event_type"] == "INCIDENT_ACTIVE"


def test_situation_report_creation_and_permissions(
    auth_headers_volunteer,
    auth_headers_citizen,
    db_session: Session,
):
    """11 & 12. Test Situation Report (SITREP) submission and timeline integration."""
    inc = incident_service.create_incident(
        db=db_session,
        title="SITREP Target Incident",
        disaster_type="flood",
        severity=7.5,
        latitude=26.0,
        longitude=78.0,
    )

    sitrep_payload = {
        "incident_id": inc.id,
        "report_type": "field",
        "summary": "Primary access bridges intact. Sector B requires water purification units.",
        "people_affected": 320,
        "people_displaced": 45,
        "casualties_reported": 0,
        "infrastructure_damage_level": "moderate",
        "medical_need_level": "low",
        "food_need_level": "high",
        "water_need_level": "critical",
        "shelter_need_level": "moderate",
        "communication_status": "operational",
    }

    # Volunteer can submit
    res_vol = client.post("/api/v1/situation-reports", json=sitrep_payload, headers=auth_headers_volunteer)
    assert res_vol.status_code == 201
    sitrep_data = res_vol.json()
    assert sitrep_data["people_affected"] == 320
    assert sitrep_data["water_need_level"] == "critical"

    # Citizen cannot submit SITREP
    res_cit = client.post("/api/v1/situation-reports", json=sitrep_payload, headers=auth_headers_citizen)
    assert res_cit.status_code == 403

    # Query SITREPs for incident
    res_inc_sitreps = client.get(f"/api/v1/situation-reports/incident/{inc.id}")
    assert res_inc_sitreps.status_code == 200
    assert len(res_inc_sitreps.json()) >= 1

    # Check that SITREP added a timeline event on the incident
    res_timeline = client.get(f"/api/v1/incidents/{inc.id}/timeline")
    events = [t["event_type"] for t in res_timeline.json()]
    assert "SITREP_SUBMITTED" in events


def test_geospatial_nearby_incidents_search(db_session: Session):
    """13 & 14. Test GET /api/v1/geo/incidents/nearby with radius, disaster_type and severity filters."""
    # Create test incident in Delhi
    inc = incident_service.create_incident(
        db=db_session,
        title="Delhi Urban Waterlogging",
        disaster_type="flood",
        severity=6.5,
        latitude=28.6139,
        longitude=77.2090,
        affected_radius_km=20.0,
    )

    # Search around Delhi (within 30km)
    res_near = client.get("/api/v1/geo/incidents/nearby?latitude=28.61&longitude=77.20&radius_km=30.0")
    assert res_near.status_code == 200
    data_near = res_near.json()
    assert data_near["count"] >= 1
    found = [i for i in data_near["results"] if i["id"] == inc.id]
    assert len(found) == 1
    assert found[0]["distance_km"] < 5.0

    # Search in Mumbai (1100km away) with 50km radius should NOT find Delhi incident
    res_far = client.get("/api/v1/geo/incidents/nearby?latitude=19.0760&longitude=72.8777&radius_km=50.0")
    assert res_far.status_code == 200
    found_far = [i for i in res_far.json()["results"] if i["id"] == inc.id]
    assert len(found_far) == 0


def test_incident_impact_zone_analysis(db_session: Session):
    """15. Test GET /api/v1/geo/incidents/{id}/impact-zone."""
    citizen = db_session.query(User).filter(User.role == "citizen").first()
    if not citizen:
        citizen = User(
            email="citizen_zone@reliefchain.ai",
            hashed_password=get_password_hash("Pass123!"),
            full_name="Zone Citizen",
            role="citizen",
            is_active=True,
        )
        db_session.add(citizen)
        db_session.commit()
        db_session.refresh(citizen)

    inc = incident_service.create_incident(
        db=db_session,
        title="Impact Zone Assessment Cyclone",
        disaster_type="cyclone",
        severity=8.2,
        latitude=13.0827,
        longitude=80.2707,
        affected_radius_km=35.0,
    )

    # Create a nearby relief request
    req = ReliefRequest(
        citizen_id=citizen.id,
        disaster_type="cyclone",
        location_name="Coastal Hamlet A",
        latitude=13.10,
        longitude=80.28,
        priority="Critical",
        status="pending",
        affected_people=120,
    )
    db_session.add(req)
    db_session.commit()

    res = client.get(f"/api/v1/geo/incidents/{inc.id}/impact-zone")
    assert res.status_code == 200
    zone = res.json()["impact_zone"]
    assert zone["incident_id"] == inc.id
    assert zone["center"]["latitude"] == inc.latitude
    assert zone["impact_metrics"]["active_sos_requests_count"] >= 1
    assert zone["impact_metrics"]["critical_sos_count"] >= 1


def test_geojson_map_feed():
    """16. Test GET /api/v1/geo/map returns GeoJSON FeatureCollection."""
    res = client.get("/api/v1/geo/map")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
    assert isinstance(data["features"], list)
    if len(data["features"]) > 0:
        f = data["features"][0]
        assert f["type"] == "Feature"
        assert "geometry" in f
        assert f["geometry"]["type"] == "Point"
        assert "coordinates" in f["geometry"]
        assert "properties" in f


def test_disaster_escalation_engine(db_session: Session, auth_headers_ngo):
    """17, 18, 19. Test escalation levels calculation, explainability reasons, and critical thresholds."""
    citizen = db_session.query(User).filter(User.role == "citizen").first()
    if not citizen:
        citizen = User(
            email="citizen_esc@reliefchain.ai",
            hashed_password=get_password_hash("Pass123!"),
            full_name="Escalation Citizen",
            role="citizen",
            is_active=True,
        )
        db_session.add(citizen)
        db_session.commit()
        db_session.refresh(citizen)

    # Create severe disaster incident
    inc = incident_service.create_incident(
        db=db_session,
        title="Critical Mega Earthquake",
        disaster_type="earthquake",
        severity=9.2,
        latitude=34.0,
        longitude=74.0,
    )

    # Add 22 high/critical SOS requests
    for i in range(22):
        req = ReliefRequest(
            citizen_id=citizen.id,
            disaster_type="earthquake",
            location_name=f"Rubble Sector {i}",
            latitude=34.01,
            longitude=74.01,
            priority="Critical",
            status="pending",
            affected_people=80,
        )
        db_session.add(req)

    # Add SITREP with casualties
    sitrep = SituationReport(
        incident_id=inc.id,
        author_id=citizen.id,
        report_type="field",
        summary="Collapsed residential structures, triage in progress.",
        casualties_reported=12,
        people_displaced=650,
        infrastructure_damage_level="catastrophic",
    )
    db_session.add(sitrep)
    db_session.commit()

    # Trigger escalation evaluation via API
    res = client.post(f"/api/v1/incidents/{inc.id}/evaluate-escalation", headers=auth_headers_ngo)
    assert res.status_code == 200
    analysis = res.json()["escalation_analysis"]
    assert analysis["incident_id"] == inc.id
    assert analysis["score"] >= 80
    assert analysis["escalation_level"] == "LEVEL_4_CRITICAL"
    assert len(analysis["reasons"]) >= 3
    assert any("severity" in r.lower() for r in analysis["reasons"])


def test_disaster_intelligence_sync_authorization(auth_headers_admin, auth_headers_citizen):
    """20. Test POST /api/v1/disaster-intelligence/sync authorization."""
    # Admin can sync
    res_admin = client.post("/api/v1/disaster-intelligence/sync?provider_name=mock_provider", headers=auth_headers_admin)
    assert res_admin.status_code == 200
    assert res_admin.json()["success"] is True

    # Citizen is forbidden
    res_cit = client.post("/api/v1/disaster-intelligence/sync?provider_name=mock_provider", headers=auth_headers_citizen)
    assert res_cit.status_code == 403


def test_command_center_summary_api():
    """21. Test GET /api/v1/command-center/summary."""
    res = client.get("/api/v1/command-center/summary")
    assert res.status_code == 200
    data = res.json()
    assert "active_incidents_count" in data
    assert "incidents_by_severity" in data
    assert "incidents_by_type" in data
    assert "critical_incidents_count" in data
    assert "unresolved_sos_requests_count" in data
    assert "volunteer_availability_count" in data
    assert "recent_situation_reports" in data
    assert "recent_timeline_activity" in data
    assert data["system_readiness"] == "OPERATIONAL"


def test_provider_registry_and_events_listing():
    """22. Test GET /api/v1/disaster-intelligence/providers and events."""
    res_prov = client.get("/api/v1/disaster-intelligence/providers")
    assert res_prov.status_code == 200
    assert "mock_provider" in res_prov.json()["providers"]

    res_events = client.get("/api/v1/disaster-intelligence/events")
    assert res_events.status_code == 200
    assert isinstance(res_events.json(), list)


def test_nonexistent_incident_returns_404(auth_headers_ngo):
    """23. Test non-existent incident IDs return 404 cleanly."""
    bad_id = "00000000-0000-0000-0000-000000000000"
    assert client.get(f"/api/v1/incidents/{bad_id}").status_code == 404
    assert client.get(f"/api/v1/incidents/{bad_id}/timeline").status_code == 404
    assert client.post(f"/api/v1/incidents/{bad_id}/verify", headers=auth_headers_ngo).status_code == 404
    assert client.get(f"/api/v1/geo/incidents/{bad_id}/impact-zone").status_code == 404


def test_incident_patch_updates_parameters(auth_headers_ngo, db_session: Session):
    """25. Test PATCH /api/v1/incidents/{id} updates parameters correctly."""
    inc = incident_service.create_incident(
        db=db_session,
        title="Patch Target Incident",
        disaster_type="wildfire",
        severity=5.0,
        latitude=12.97,
        longitude=77.59,
    )

    patch_payload = {
        "title": "Updated Scrub Wildfire Incident",
        "severity": 6.5,
        "affected_radius_km": 30.0,
        "description": "Expanded containment perimeter.",
    }
    res = client.patch(f"/api/v1/incidents/{inc.id}", json=patch_payload, headers=auth_headers_ngo)
    assert res.status_code == 200
    updated = res.json()
    assert updated["title"] == "Updated Scrub Wildfire Incident"
    assert updated["severity"] == 6.5
    assert updated["affected_radius_km"] == 30.0


def test_incident_direct_action_endpoints(auth_headers_ngo, db_session: Session):
    """26. Test /verify, /activate, /resolve action endpoints."""
    inc = incident_service.create_incident(
        db=db_session,
        title="Action Endpoints Test Incident",
        disaster_type="storm",
        severity=6.0,
        latitude=20.0,
        longitude=75.0,
    )
    assert inc.status == "DETECTED"

    # Verify
    res_v = client.post(f"/api/v1/incidents/{inc.id}/verify", json={"note": "Confirmed by sensor"}, headers=auth_headers_ngo)
    assert res_v.status_code == 200
    assert res_v.json()["status"] == "VERIFIED"

    # Activate
    res_a = client.post(f"/api/v1/incidents/{inc.id}/activate", json={"note": "Field squads deployed"}, headers=auth_headers_ngo)
    assert res_a.status_code == 200
    assert res_a.json()["status"] == "ACTIVE"

    # Resolve
    res_r = client.post(f"/api/v1/incidents/{inc.id}/resolve", json={"note": "Threat neutralized"}, headers=auth_headers_ngo)
    assert res_r.status_code == 200
    assert res_r.json()["status"] == "RESOLVED"


def test_websocket_incident_event_envelope_structure():
    """27. Test WebSocket event envelope structure conforms to schema standards."""
    envelope = {
        "event": "incident.escalated",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": "test-req-id-1234",
        "data": {
            "incident_id": "inc-001",
            "escalation_level": "LEVEL_4_CRITICAL",
            "score": 92,
        },
    }
    assert envelope["event"] == "incident.escalated"
    assert "timestamp" in envelope
    assert "data" in envelope
    assert envelope["data"]["escalation_level"] == "LEVEL_4_CRITICAL"


def test_backward_compatibility_existing_geo_endpoints():
    """28. Backward compatibility: verify previous geo endpoints work intact."""
    res_reqs = client.get("/api/v1/geo/nearby-requests?latitude=28.61&longitude=77.20&radius_km=25.0")
    assert res_reqs.status_code == 200
    assert res_reqs.json()["success"] is True

    res_hotspots = client.get("/api/v1/geo/disaster-hotspots")
    assert res_hotspots.status_code == 200
    assert res_hotspots.json()["success"] is True

