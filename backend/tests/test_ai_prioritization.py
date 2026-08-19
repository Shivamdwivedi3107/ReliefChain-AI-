import pytest
from app.services.ai_service import (
    calculate_priority_score_details,
    predict_emergency_priority,
    DISASTER_RISK_WEIGHTS,
)


def test_ai_priority_calculation_critical_medical():
    """Verify that severe medical trauma with trapped victims scores in Critical triage tier."""
    result = calculate_priority_score_details(
        disaster_type="flood",
        affected_people=45,
        location_risk_score=7.5,
        medical_needed=1,
        water_needed=1,
        food_needed=1,
        vulnerable_population=1,
        time_elapsed_hours=5.0,
        request_id="req-999",
    )

    assert result["priority_level"] == "Critical"
    assert result["priority_slug"] == "critical"
    assert result["priority_score"] >= 80.0
    assert result["explanation"]["medical_urgency_factor"] == 20.0
    assert result["explanation"]["affected_people"] == 45
    assert result["confidence"] >= 0.90


def test_ai_priority_calculation_low_urgency():
    """Verify that minor disaster without medical trauma scores as Low/Medium."""
    result = calculate_priority_score_details(
        disaster_type="other",
        affected_people=2,
        location_risk_score=1.0,
        medical_needed=0,
        water_needed=0,
        food_needed=0,
        vulnerable_population=0,
        time_elapsed_hours=0.5,
    )

    assert result["priority_level"] in ["Low", "Medium"]
    assert result["priority_score"] < 50.0


def test_predict_emergency_priority_backward_compatibility():
    """Test backward compatible signature returning (slug, confidence, factors)."""
    slug, confidence, factors = predict_emergency_priority(
        disaster_type="earthquake",
        affected_people=100,
        medical_needed=1,
    )

    assert slug in ["critical", "high"]
    assert isinstance(confidence, float)
    assert "disaster_base_risk" in factors
    assert "calculated_priority_score" in factors


def test_ai_predict_priority_api_endpoint(client):
    """Test the POST /api/v1/ai/predict-priority API endpoint."""
    payload = {
        "disaster_type": "tsunami",
        "affected_people": 250,
        "location_risk_score": 9.0,
        "medical_needed": 1,
        "water_needed": 1,
        "food_needed": 1,
        "vulnerable_population": 1,
        "time_elapsed_hours": 3.0,
        "request_id": "test-req-ai-1",
    }
    response = client.post("/api/v1/ai/predict-priority", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["priority_level"] == "Critical"
    assert data["priority_score"] >= 80.0
    assert "explanation" in data
    assert "decision_support_disclaimer" in data
