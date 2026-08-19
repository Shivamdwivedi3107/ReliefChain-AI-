import os
from typing import Dict, Any, Tuple, Optional
from app.core.logging import logger

# Disaster base risk weights (base points out of 20)
DISASTER_RISK_WEIGHTS = {
    "tsunami": 20.0,
    "earthquake": 18.0,
    "cyclone": 16.0,
    "flood": 15.0,
    "wildfire": 15.0,
    "landslide": 14.0,
    "other": 10.0,
}


def calculate_priority_score_details(
    disaster_type: str,
    affected_people: int,
    location_risk_score: float = 1.0,
    food_needed: int = 0,
    water_needed: int = 0,
    medical_needed: int = 0,
    vulnerable_population: int = 0,
    time_elapsed_hours: float = 0.0,
    request_id: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Transparent Decision Support System (DSS) scoring engine calculating
    a standardized 0-100 score with granular explainability and priority level.
    """
    dtype = str(disaster_type or "").lower().strip()
    disaster_score = DISASTER_RISK_WEIGHTS.get(dtype, 10.0)  # Max 20

    # People factor: logarithmic / stepped scaling up to 25 points
    if affected_people >= 200:
        people_score = 25.0
    elif affected_people >= 50:
        people_score = 20.0
    elif affected_people >= 20:
        people_score = 15.0
    elif affected_people >= 5:
        people_score = 10.0
    else:
        people_score = 5.0

    # Urgency & resource needs (Max 35 points)
    medical_score = 20.0 if medical_needed else 0.0
    water_score = 8.0 if water_needed else 0.0
    food_score = 7.0 if food_needed else 0.0

    # Vulnerability (elderly, infants, pregnant) (Max 10 points)
    vulnerable_score = 10.0 if vulnerable_population else 0.0

    # Location Risk (0-10 scale mapped to max 5 points)
    location_score = min(max(float(location_risk_score), 0.0) * 0.5, 5.0)

    # Waiting Time Decay (hours passed * 0.5, max 5 points)
    time_score = min(max(float(time_elapsed_hours), 0.0) * 0.5, 5.0)

    total_score = min(
        100.0,
        disaster_score
        + people_score
        + medical_score
        + water_score
        + food_score
        + vulnerable_score
        + location_score
        + time_score
    )

    if total_score >= 80.0 or (medical_needed and affected_people >= 20):
        priority_level = "Critical"
        priority_slug = "critical"
    elif total_score >= 60.0:
        priority_level = "High"
        priority_slug = "high"
    elif total_score >= 40.0:
        priority_level = "Medium"
        priority_slug = "medium"
    else:
        priority_level = "Low"
        priority_slug = "low"

    urgency_desc = "Severe / Life Threatening" if medical_needed else ("High" if total_score >= 60 else "Moderate")

    explanation = {
        "urgency": urgency_desc,
        "affected_people": affected_people,
        "disaster_severity": dtype.title(),
        "medical_urgency_factor": medical_score,
        "water_urgency_factor": water_score,
        "food_urgency_factor": food_score,
        "vulnerable_population_presence": vulnerable_score,
        "location_risk_factor": round(location_score, 1),
        "waiting_time_urgency": round(time_score, 1),
    }

    return {
        "request_id": request_id,
        "priority_score": round(total_score, 1),
        "priority_level": priority_level,
        "priority_slug": priority_slug,
        "explanation": explanation,
        "confidence": 0.94 if priority_level in ["Critical", "High"] else 0.88,
    }


def predict_emergency_priority(
    disaster_type: str,
    affected_people: int,
    location_risk_score: float = 1.0,
    food_needed: int = 0,
    water_needed: int = 0,
    medical_needed: int = 0,
    vulnerable_population: int = 0,
    time_elapsed_hours: float = 0.0,
) -> Tuple[str, float, Dict[str, float]]:
    """
    Backward-compatible triage method returning (priority_slug, confidence, contributing_factors).
    """
    details = calculate_priority_score_details(
        disaster_type=disaster_type,
        affected_people=affected_people,
        location_risk_score=location_risk_score,
        food_needed=food_needed,
        water_needed=water_needed,
        medical_needed=medical_needed,
        vulnerable_population=vulnerable_population,
        time_elapsed_hours=time_elapsed_hours,
    )

    factors = {
        "disaster_base_risk": DISASTER_RISK_WEIGHTS.get(disaster_type.lower(), 10.0),
        "affected_population_weight": float(details["explanation"]["affected_people"]),
        "medical_urgency": float(details["explanation"]["medical_urgency_factor"]),
        "potable_water_urgency": float(details["explanation"]["water_urgency_factor"]),
        "food_urgency": float(details["explanation"]["food_urgency_factor"]),
        "vulnerable_population_presence": float(details["explanation"]["vulnerable_population_presence"]),
        "location_hazard_score": float(details["explanation"]["location_risk_factor"]),
        "calculated_priority_score": float(details["priority_score"]),
    }

    return details["priority_slug"], details["confidence"], factors
