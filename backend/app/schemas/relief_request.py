from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema
from app.schemas.user import UserOut
from app.schemas.organization import OrganizationOut
from app.schemas.disaster import DisasterOut


class ReliefRequestBase(BaseSchema):
    disaster_type: str = Field(..., min_length=2, max_length=50)
    location_name: str = Field(..., min_length=2, max_length=200)
    latitude: float
    longitude: float
    affected_people: int = Field(default=1, ge=1)
    required_resources: List[Dict[str, Any]] = Field(default_factory=list)
    urgency_description: Optional[str] = None
    image_reference: Optional[str] = None
    disaster_id: Optional[str] = None


class ReliefRequestCreate(ReliefRequestBase):
    pass


class ReliefRequestUpdate(BaseSchema):
    status: Optional[str] = None  # pending, under_review, assigned, in_progress, completed, rejected
    priority: Optional[str] = None
    assigned_organization_id: Optional[str] = None
    assigned_volunteer_id: Optional[str] = None
    urgency_description: Optional[str] = None
    affected_people: Optional[int] = None


class ReliefRequestAssign(BaseSchema):
    assigned_organization_id: Optional[str] = None
    assigned_volunteer_id: Optional[str] = None
    notes: Optional[str] = None


class ReliefRequestOut(ReliefRequestBase):
    id: str
    citizen_id: str
    priority: str
    status: str
    assigned_organization_id: Optional[str] = None
    assigned_volunteer_id: Optional[str] = None
    ai_predicted_priority: Optional[str] = None
    ai_confidence: Optional[float] = None
    ai_factors: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime
    citizen: Optional[UserOut] = None
    assigned_volunteer: Optional[UserOut] = None
    assigned_organization: Optional[OrganizationOut] = None
    disaster: Optional[DisasterOut] = None
