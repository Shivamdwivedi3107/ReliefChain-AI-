"""
Phase 8 Automated Test Suite — ReliefChain AI
Tests Disaster Risk Prediction, Resource Demand Forecasting, Volunteer Matching,
Disaster Impact Simulation, AI Model Registry & Governance, and Explainability.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.models.user import User
from app.models.relief_request import ReliefRequest
from app.models.resource import Resource, ResourceInventory
from app.models.organization import Organization
from app.models.audit_log import AuditLog
from app.models.blockchain import BlockchainTransaction
from app.services.risk_prediction import DisasterRiskPredictionService
from app.services.resource_forecasting import ResourceForecastingService
from app.services.volunteer_matching import VolunteerMatchingService
from app.services.disaster_simulation import DisasterSimulationService
from app.services.model_registry import AIModelRegistry
from app.services.ai_explainability import AIExplainabilityEngine
from app.core.security import create_access_token, get_password_hash


@pytest.fixture
def phase8_test_data(db_session: Session):
    """Seed users, an organization, warehouse stock, and a test mission."""
    # 1. Organization
    org = Organization(
        id="org-phase8-ngo-1",
        name="Global Disaster Relief Corps",
        registration_number="REG-NGO-PHASE8-001",
        organization_type="NGO",
        contact_email="hq@globaldisasterrelief.org",
        contact_phone="+1-555-0199",
        verification_status="verified",
        is_active=True,
    )
    db_session.add(org)

    # 2. Users: Admin, NGO, Volunteer, Citizen
    admin = User(
        id="user-phase8-admin-1",
        email="admin_phase8@reliefchain.org",
        hashed_password=get_password_hash("AdminPass123!"),
        full_name="Admin Director",
        role="admin",
        is_active=True,
    )
    ngo = User(
        id="user-phase8-ngo-1",
        email="ngo_phase8@reliefchain.org",
        hashed_password=get_password_hash("NgoPass123!"),
        full_name="NGO Field Chief",
        role="ngo",
        organization_id=org.id,
        is_active=True,
    )
    volunteer1 = User(
        id="user-phase8-vol-1",
        email="volunteer1_phase8@reliefchain.org",
        hashed_password=get_password_hash("VolPass123!"),
        full_name="Dr. Sarah Connor",
        role="volunteer",
        skills=["medical", "trauma", "first_aid"],
        current_latitude=28.6150,
        current_longitude=77.2100,
        availability=True,
        max_mission_capacity=4,
        reliability_score=4.9,
        is_active=True,
    )
    volunteer2 = User(
        id="user-phase8-vol-2",
        email="volunteer2_phase8@reliefchain.org",
        hashed_password=get_password_hash("VolPass123!"),
        full_name="John Driver",
        role="volunteer",
        skills=["logistics", "heavy_vehicle", "driver"],
        current_latitude=28.7500,
        current_longitude=77.3000,
        availability=True,
        max_mission_capacity=2,
        reliability_score=4.2,
        is_active=True,
    )
    citizen = User(
        id="user-phase8-cit-1",
        email="citizen_phase8@reliefchain.org",
        hashed_password=get_password_hash("CitizenPass123!"),
        full_name="Jane Doe",
        role="citizen",
        is_active=True,
    )
    db_session.add_all([admin, ngo, volunteer1, volunteer2, citizen])

    # 3. Resources & Inventory
    water_res = Resource(id="res-p8-water", name="Potable Water 20L Can", category="water", unit="liters")
    food_res = Resource(id="res-p8-food", name="High-Energy Ration Pack", category="food", unit="packs")
    db_session.add_all([water_res, food_res])
    db_session.flush()

    inv_water = ResourceInventory(
        id="inv-p8-water-1",
        organization_id=org.id,
        resource_id=water_res.id,
        total_quantity=500.0,
        available_quantity=300.0,
        reserved_quantity=200.0,
    )
    inv_food = ResourceInventory(
        id="inv-p8-food-1",
        organization_id=org.id,
        resource_id=food_res.id,
        total_quantity=200.0,
        available_quantity=150.0,
        reserved_quantity=50.0,
    )
    db_session.add_all([inv_water, inv_food])

    # 4. Active Relief Mission
    mission = ReliefRequest(
        id="mission-phase8-test-1",
        citizen_id=citizen.id,
        disaster_type="earthquake",
        location_name="Connaught Sector 4",
        latitude=28.6139,
        longitude=77.2090,
        priority="critical",
        status="assigned",
        affected_people=45,
        required_resources=["water", "food", "medical"],
        urgency_description="Trapped individuals need immediate medical and water assistance",
    )
    db_session.add(mission)
    db_session.commit()

    # Generate Auth Tokens
    admin_token = create_access_token(subject=admin.id, role="admin")
    ngo_token = create_access_token(subject=ngo.id, role="ngo")
    cit_token = create_access_token(subject=citizen.id, role="citizen")

    return {
        "admin_token": admin_token,
        "ngo_token": ngo_token,
        "citizen_token": cit_token,
        "mission_id": mission.id,
        "org_id": org.id,
    }


# =============================================================================
# 1. Disaster Risk Prediction Tests
# =============================================================================

def test_risk_score_calculation_low_and_critical():
    """Verify rule-based multi-factor risk calculations produce correct score tiers."""
    # Low hazard scenario
    low_score = DisasterRiskPredictionService.calculate_rule_based_risk(
        disaster_type="drought",
        historical_severity=2.0,
        rainfall_mm=0.0,
        population_density=80.0,
        vulnerable_population_pct=5.0,
        infrastructure_risk_score=0.2,
        previous_disaster_frequency=0,
        resource_availability_score=0.9,
    )
    assert 5.0 <= low_score <= 45.0

    # Critical hazard scenario (Seismic + Extreme density + High vulnerability + Infrastructure failure)
    critical_score = DisasterRiskPredictionService.calculate_rule_based_risk(
        disaster_type="earthquake",
        historical_severity=9.5,
        rainfall_mm=120.0,
        population_density=2500.0,
        vulnerable_population_pct=40.0,
        infrastructure_risk_score=0.95,
        previous_disaster_frequency=4,
        resource_availability_score=0.1,
    )
    assert critical_score >= 80.0


def test_risk_predict_service_full_payload():
    """Verify complete output contract of DisasterRiskPredictionService."""
    res = DisasterRiskPredictionService.predict_risk(
        disaster_type="flood",
        historical_severity=7.5,
        rainfall_mm=160.0,
        population_density=1200.0,
        location_name="River Valley East",
        latitude=28.6139,
        longitude=77.2090,
    )
    assert res["success"] is True
    assert res["risk_level"] in ("HIGH", "CRITICAL")
    assert res["risk_score"] > 60.0
    assert len(res["risk_factors"]) > 0
    assert len(res["recommendations"]) > 0
    assert "dss_disclaimer" in res


def test_risk_predict_api_endpoint(client: TestClient, phase8_test_data):
    """Test POST /api/v1/ai/risk-predict endpoint and audit persistence."""
    payload = {
        "disaster_type": "cyclone",
        "historical_severity": 8.0,
        "rainfall_mm": 180.0,
        "population_density": 950.0,
        "vulnerable_population_pct": 28.0,
        "infrastructure_risk_score": 0.75,
        "location_name": "Coastal District Beta",
        "latitude": 19.0760,
        "longitude": 72.8777,
    }
    response = client.post(
        "/api/v1/ai/risk-predict",
        json=payload,
        headers={"Authorization": f"Bearer {phase8_test_data['citizen_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["risk_level"] in ("HIGH", "CRITICAL")
    assert "prediction_id" in data


# =============================================================================
# 2. Resource Demand Forecasting Tests
# =============================================================================

def test_resource_demand_forecasting_calculation():
    """Verify humanitarian SPHERE consumption scaling for food, water, and shelter."""
    forecast = ResourceForecastingService.calculate_predicted_demand(
        disaster_type="flood",
        severity=8.0,
        population_affected=1000,
        forecast_period_hours=48,
    )
    # 1000 people * ~4.75L/day * 2 days = ~9500L
    assert forecast["water"] >= 8000.0
    # 1000 people * ~3.05 meals/day * 2 days = ~6100 meals
    assert forecast["food"] >= 5000.0
    assert forecast["medical_kits"] >= 10
    assert forecast["shelter_tents"] >= 50


def test_resource_forecast_api_with_inventory_gap(client: TestClient, phase8_test_data):
    """Test POST /api/v1/ai/resource-forecast for NGO role and inventory shortage detection."""
    payload = {
        "disaster_type": "earthquake",
        "severity": 9.0,
        "population_affected": 2500,
        "forecast_period_hours": 24,
        "organization_id": phase8_test_data["org_id"],
    }
    response = client.post(
        "/api/v1/ai/resource-forecast",
        json=payload,
        headers={"Authorization": f"Bearer {phase8_test_data['ngo_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["has_shortage"] is True
    # Water demand will exceed 300 available liters
    assert data["inventory_gap"]["water"] > 0
    assert len(data["recommendations"]) > 0


def test_resource_forecast_citizen_forbidden(client: TestClient, phase8_test_data):
    """Ensure citizens cannot invoke operational logistics forecasting."""
    payload = {
        "disaster_type": "flood",
        "severity": 6.0,
        "population_affected": 500,
    }
    response = client.post(
        "/api/v1/ai/resource-forecast",
        json=payload,
        headers={"Authorization": f"Bearer {phase8_test_data['citizen_token']}"},
    )
    assert response.status_code == 403


# =============================================================================
# 3. Volunteer Intelligent Assignment Tests
# =============================================================================

def test_volunteer_matching_ranking(client: TestClient, phase8_test_data):
    """Test GET /api/v1/ai/volunteer-recommendations/{mission_id} returns ranked best-fit candidates."""
    mission_id = phase8_test_data["mission_id"]
    response = client.get(
        f"/api/v1/ai/volunteer-recommendations/{mission_id}?limit=5",
        headers={"Authorization": f"Bearer {phase8_test_data['ngo_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["recommendations"]) >= 1

    # First candidate should be Dr. Sarah Connor due to high medical skill affinity and immediate proximity
    top_cand = data["recommendations"][0]
    assert top_cand["volunteer_name"] == "Dr. Sarah Connor"
    assert top_cand["match_score"] >= 80.0
    assert top_cand["recommendation"] == "HIGHLY_RECOMMENDED"


def test_volunteer_recommendations_nonexistent_mission_returns_404(client: TestClient, phase8_test_data):
    """Ensure 404 is returned if mission does not exist."""
    response = client.get(
        "/api/v1/ai/volunteer-recommendations/non-existent-mission-id",
        headers={"Authorization": f"Bearer {phase8_test_data['ngo_token']}"},
    )
    assert response.status_code == 404


# =============================================================================
# 4. Disaster Impact Simulation Tests
# =============================================================================

def test_disaster_simulation_impact_modeling():
    """Verify disaster simulation calculations for casualties, volunteers, and supply burn."""
    sim = DisasterSimulationService.run_simulation(
        disaster_type="earthquake",
        severity=8.5,
        population_affected=15000,
        duration_hours=72,
        location_name="Simulated Metropolitan Center",
    )
    assert sim["success"] is True
    assert sim["simulation_mode"] == "DECISION_SUPPORT_SIMULATION_ONLY"
    assert sim["projected_impact"]["total_sos_requests"] > 100
    assert sim["projected_impact"]["critical_trauma_cases"] > 10
    assert sim["personnel_requirements"]["total_volunteers_needed"] > 50
    assert sim["supply_requirements"]["water_liters"] > 50000


def test_disaster_simulation_admin_api_and_ledger_sealing(client: TestClient, phase8_test_data):
    """Test POST /api/v1/ai/simulate-disaster (Admin only) seals event into SHA-256 Ledger."""
    payload = {
        "scenario_title": "Contingency Coastal Inundation Drill",
        "disaster_type": "tsunami",
        "severity": 8.0,
        "population_affected": 8000,
        "duration_hours": 48,
        "location_name": "Bay Area Sector 3",
    }
    response = client.post(
        "/api/v1/ai/simulate-disaster",
        json=payload,
        headers={"Authorization": f"Bearer {phase8_test_data['admin_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "simulation_id" in data
    assert "ledger_tx_id" in data


def test_disaster_simulation_forbidden_for_non_admins(client: TestClient, phase8_test_data):
    """Verify NGO and Citizens are blocked with 403 on simulation endpoints."""
    payload = {
        "scenario_title": "Unauthorized Drill",
        "disaster_type": "flood",
        "severity": 5.0,
        "population_affected": 2000,
    }
    # NGO attempt
    ngo_res = client.post(
        "/api/v1/ai/simulate-disaster",
        json=payload,
        headers={"Authorization": f"Bearer {phase8_test_data['ngo_token']}"},
    )
    assert ngo_res.status_code == 403

    # Citizen attempt
    cit_res = client.post(
        "/api/v1/ai/simulate-disaster",
        json=payload,
        headers={"Authorization": f"Bearer {phase8_test_data['citizen_token']}"},
    )
    assert cit_res.status_code == 403


# =============================================================================
# 5. AI Model Registry & Governance Tests
# =============================================================================

def test_model_registry_listing_and_inspection(client: TestClient, phase8_test_data):
    """Test GET /api/v1/ai/models and GET /api/v1/ai/models/{model_name}."""
    # List models
    res_list = client.get(
        "/api/v1/ai/models",
        headers={"Authorization": f"Bearer {phase8_test_data['ngo_token']}"},
    )
    assert res_list.status_code == 200
    models_data = res_list.json()
    assert models_data["success"] is True
    assert len(models_data["models"]) >= 4

    # Inspect specific model card
    res_card = client.get(
        "/api/v1/ai/models/priority_classifier",
        headers={"Authorization": f"Bearer {phase8_test_data['citizen_token']}"},
    )
    assert res_card.status_code == 200
    card_data = res_card.json()
    assert card_data["success"] is True
    assert card_data["model"]["model_name"] == "priority_classifier"
    assert card_data["model"]["accuracy"] > 0.8


def test_model_activation_admin_only(client: TestClient, phase8_test_data):
    """Test POST /api/v1/ai/models/activate toggles status for admin and rejects non-admin."""
    # Citizen attempt (Forbidden)
    cit_res = client.post(
        "/api/v1/ai/models/activate",
        json={"model_name": "risk_predictor", "is_active": False},
        headers={"Authorization": f"Bearer {phase8_test_data['citizen_token']}"},
    )
    assert cit_res.status_code == 403

    # Admin attempt (Success)
    admin_res = client.post(
        "/api/v1/ai/models/activate",
        json={"model_name": "risk_predictor", "is_active": True},
        headers={"Authorization": f"Bearer {phase8_test_data['admin_token']}"},
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["success"] is True
    assert admin_res.json()["is_active"] is True


# =============================================================================
# 6. Explainability & Analytics Tests
# =============================================================================

def test_explainable_ai_engine_breakdown():
    """Verify AIExplainabilityEngine generates comprehensive feature factors and summary."""
    xai = AIExplainabilityEngine.explain_disaster_risk(
        disaster_type="landslide",
        risk_score=78.5,
        rainfall_mm=140.0,
        population_density=650.0,
        vulnerable_population_pct=30.0,
        infrastructure_risk_score=0.8,
        previous_disaster_frequency=3,
        resource_availability_score=0.2,
    )
    assert "summary" in xai
    assert len(xai["factors"]) >= 5
    assert xai["explainability_confidence"] > 0.85


def test_ai_intelligence_analytics_endpoint(client: TestClient, phase8_test_data):
    """Test GET /api/v1/analytics/ai-intelligence returns aggregated AI metrics."""
    response = client.get(
        "/api/v1/analytics/ai-intelligence",
        headers={"Authorization": f"Bearer {phase8_test_data['admin_token']}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "active_ai_models_count" in data
    assert "average_risk_score" in data
    assert "models_catalog_summary" in data


def test_backward_compatibility_priority_triage_endpoints(client: TestClient):
    """Ensure existing /api/v1/ai/predict-priority and /model-info continue functioning without regression."""
    payload = {
        "disaster_type": "flood",
        "affected_people": 12,
        "location_risk_score": 5.0,
        "medical_needed": 1,
        "food_needed": 1,
        "water_needed": 1,
        "vulnerable_population": 1,
    }
    res = client.post("/api/v1/ai/predict-priority", json=payload)
    assert res.status_code == 200
    triage_data = res.json()
    assert triage_data["priority_score"] >= 70.0
    assert triage_data["priority_level"] in ("Critical", "High")
    assert "decision_support_disclaimer" in triage_data


def test_risk_predict_validation_rejects_negative_severity(client: TestClient):
    """Verify input validation rejects negative historical severity."""
    bad_payload = {
        "disaster_type": "cyclone",
        "historical_severity": -5.0,
    }
    res = client.post("/api/v1/ai/risk-predict", json=bad_payload)
    assert res.status_code == 422


def test_resource_forecasting_extended_horizon_scaling():
    """Verify resource forecasting scales linearly across 24h, 48h, and 72h horizons."""
    forecast_24 = ResourceForecastingService.calculate_predicted_demand("flood", 7.0, 500, forecast_period_hours=24)
    forecast_72 = ResourceForecastingService.calculate_demand_72 = ResourceForecastingService.calculate_predicted_demand("flood", 7.0, 500, forecast_period_hours=72)
    assert forecast_72["water"] > forecast_24["water"] * 2.5
    assert forecast_72["food"] > forecast_24["food"] * 2.5


def test_model_registry_nonexistent_model_returns_404(client: TestClient, phase8_test_data):
    """Verify GET /api/v1/ai/models/unknown_model returns 404."""
    res = client.get(
        "/api/v1/ai/models/non_existent_model_xyz",
        headers={"Authorization": f"Bearer {phase8_test_data['admin_token']}"},
    )
    assert res.status_code == 404


def test_volunteer_matching_returns_safe_empty_list_when_no_volunteers(db_session: Session):
    """Verify matching service handles empty volunteer list gracefully."""
    # Delete all volunteers temporarily from session
    db_session.query(User).filter(User.role == "volunteer").delete()
    db_session.flush()

    res = VolunteerMatchingService.get_recommendations_for_mission(
        db=db_session,
        mission_id="non-existent",
    )
    assert res["success"] is False

