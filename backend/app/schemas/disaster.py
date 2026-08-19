from typing import Optional
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema


class DisasterBase(BaseSchema):
    title: str = Field(..., min_length=2, max_length=150)
    disaster_type: str = Field(..., min_length=2, max_length=50)  # flood, earthquake, cyclone, wildfire, landslide, other
    severity: str = Field(default="medium")  # low, medium, high, critical
    location_name: str = Field(..., min_length=2, max_length=200)
    latitude: float
    longitude: float
    radius_km: float = 10.0
    description: Optional[str] = None


class DisasterCreate(DisasterBase):
    started_at: Optional[datetime] = None


class DisasterUpdate(BaseSchema):
    title: Optional[str] = None
    disaster_type: Optional[str] = None
    severity: Optional[str] = None
    status: Optional[str] = None
    location_name: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    radius_km: Optional[float] = None
    description: Optional[str] = None
    resolved_at: Optional[datetime] = None


class DisasterOut(DisasterBase):
    id: str
    status: str
    started_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
