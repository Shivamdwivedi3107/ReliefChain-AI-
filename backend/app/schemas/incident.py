from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class DisasterEventBase(BaseModel):
    source: str = "mock_provider"
    external_id: Optional[str] = None
    disaster_type: str = "flood"
    severity: float = Field(..., ge=1.0, le=10.0)
    title: str
    description: Optional[str] = None
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    affected_radius_km: float = Field(15.0, ge=0.5, le=500.0)
    status: str = "active"
    confidence_score: float = Field(0.85, ge=0.0, le=1.0)
    raw_metadata: Optional[Dict[str, Any]] = None


class DisasterEventOut(DisasterEventBase):
    id: str
    started_at: datetime
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class IncidentCreate(BaseModel):
    title: str
    disaster_type: str = "flood"
    severity: float = Field(5.0, ge=1.0, le=10.0)
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    affected_radius_km: float = Field(10.0, ge=0.5, le=500.0)
    event_id: Optional[str] = None
    organization_id: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class IncidentUpdate(BaseModel):
    title: Optional[str] = None
    disaster_type: Optional[str] = None
    severity: Optional[float] = Field(None, ge=1.0, le=10.0)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    affected_radius_km: Optional[float] = Field(None, ge=0.5, le=500.0)
    organization_id: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    escalation_level: Optional[str] = None


class IncidentTransitionAction(BaseModel):
    note: Optional[str] = None


class IncidentTimelineOut(BaseModel):
    id: str
    incident_id: str
    event_type: str
    message: str
    actor_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IncidentOut(BaseModel):
    id: str
    event_id: Optional[str] = None
    title: str
    disaster_type: str
    severity: float
    status: str
    escalation_level: str
    latitude: float
    longitude: float
    affected_radius_km: float
    verified_by_user_id: Optional[str] = None
    resolved_by_user_id: Optional[str] = None
    organization_id: Optional[str] = None
    description: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class SituationReportCreate(BaseModel):
    incident_id: str
    report_type: str = Field("field", description="initial, update, field, final")
    summary: str
    people_affected: int = Field(0, ge=0)
    people_displaced: int = Field(0, ge=0)
    casualties_reported: int = Field(0, ge=0)
    infrastructure_damage_level: str = "moderate"
    medical_need_level: str = "moderate"
    food_need_level: str = "moderate"
    water_need_level: str = "moderate"
    shelter_need_level: str = "moderate"
    communication_status: str = "operational"
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class SituationReportOut(SituationReportCreate):
    id: str
    author_id: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)



class CommandCenterSummaryOut(BaseModel):
    active_incidents_count: int
    incidents_by_severity: Dict[str, int]
    incidents_by_type: Dict[str, int]
    critical_incidents_count: int
    unresolved_sos_requests_count: int
    volunteer_availability_count: int
    current_escalation_distribution: Dict[str, int]
    recent_situation_reports: List[Dict[str, Any]]
    recent_timeline_activity: List[Dict[str, Any]]
    system_readiness: str = "OPERATIONAL"
