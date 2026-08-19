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


class AIRiskPredictRequest(BaseSchema):
    disaster_type: str = Field(..., min_length=2, max_length=50, description="Type of disaster event")
    historical_severity: float = Field(default=5.0, ge=1.0, le=10.0, description="Past severity on 1-10 scale")
    rainfall_mm: float = Field(default=0.0, ge=0.0, description="Current / 24h forecasted precipitation in mm")
    temperature_c: float = Field(default=25.0, description="Ambient temperature in degrees Celsius")
    population_density: float = Field(default=500.0, ge=0.0, description="Estimated persons per sq km")
    vulnerable_population_pct: float = Field(default=15.0, ge=0.0, le=100.0, description="Percentage of elderly/infants/disabled")
    infrastructure_risk_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Structural fragility factor (0 to 1)")
    previous_disaster_frequency: int = Field(default=1, ge=0, description="Past disaster incidents in zone")
    resource_availability_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Local warehouse cushion (0 to 1)")
    location_name: Optional[str] = Field(default="", description="Location or administrative sector name")
    latitude: Optional[float] = Field(default=None, description="GPS Latitude")
    longitude: Optional[float] = Field(default=None, description="GPS Longitude")


class AIResourceForecastRequest(BaseSchema):
    disaster_type: str = Field(..., min_length=2, max_length=50)
    severity: float = Field(default=5.0, ge=1.0, le=10.0)
    population_affected: int = Field(..., ge=1)
    active_sos_requests: int = Field(default=0, ge=0)
    disaster_duration_hours: int = Field(default=24, ge=1)
    forecast_period_hours: int = Field(default=24, ge=1, le=168)
    organization_id: Optional[str] = None


class AIDisasterSimulationRequest(BaseSchema):
    scenario_title: str = Field(default="Contingency Scenario A", min_length=2, max_length=150)
    disaster_type: str = Field(..., min_length=2, max_length=50)
    severity: float = Field(default=6.0, ge=1.0, le=10.0)
    population_affected: int = Field(..., ge=10)
    duration_hours: int = Field(default=48, ge=6, le=720)
    location_name: str = Field(default="Metropolitan Sector 1", min_length=2, max_length=200)


class AIModelActivateRequest(BaseSchema):
    model_name: str = Field(..., min_length=2, max_length=100)
    is_active: bool = Field(default=True)
