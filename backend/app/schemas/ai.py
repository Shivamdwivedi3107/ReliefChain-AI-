from typing import Optional, Dict, Any, List
from pydantic import Field
from app.schemas.common import BaseSchema


class AIPriorityPredictRequest(BaseSchema):
    disaster_type: str = Field(..., min_length=2, max_length=50)
    affected_people: int = Field(default=1, ge=1)
    location_risk_score: float = Field(default=1.0, ge=0.0, le=10.0)
    food_needed: int = Field(default=0, ge=0, le=1)
    water_needed: int = Field(default=0, ge=0, le=1)
    medical_needed: int = Field(default=0, ge=0, le=1)
    vulnerable_population: int = Field(default=0, ge=0, le=1)  # elderly / infants / disabled
    time_elapsed_hours: float = Field(default=0.0, ge=0.0)
    request_id: Optional[Any] = None


class AIPriorityPredictResponse(BaseSchema):
    request_id: Optional[Any] = None
    priority_score: float = Field(..., ge=0.0, le=100.0, description="0 to 100 triage priority score")
    priority_level: str = Field(..., description="Critical, High, Medium, Low")
    predicted_priority: str = Field(..., description="Slug: critical, high, medium, low")
    confidence_score: float
    explanation: Dict[str, Any]
    contributing_factors: Dict[str, float]
    model_version: str = "1.2.0-dss-rule-engine"
    decision_support_disclaimer: str = (
        "This AI priority score is a Decision Support System (DSS) recommendation and must not "
        "substitute professional emergency service triage."
    )
