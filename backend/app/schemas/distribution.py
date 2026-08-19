from typing import Optional
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema
from app.schemas.user import UserOut
from app.schemas.organization import OrganizationOut
from app.schemas.resource import ResourceOut
from app.schemas.relief_request import ReliefRequestOut


class DistributionBase(BaseSchema):
    relief_request_id: str
    resource_id: str
    organization_id: str
    quantity: float = Field(..., gt=0)
    volunteer_id: Optional[str] = None
    recipient_id: Optional[str] = None
    dispatch_location: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None


class DistributionCreate(DistributionBase):
    pass


class DistributionUpdate(BaseSchema):
    status: Optional[str] = None  # scheduled, dispatched, delivered, verified, cancelled
    volunteer_id: Optional[str] = None
    recipient_id: Optional[str] = None
    dispatch_location: Optional[str] = None
    delivery_latitude: Optional[float] = None
    delivery_longitude: Optional[float] = None
    record_hash: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    qr_token: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None


class DistributionOut(DistributionBase):
    id: str
    status: str
    record_hash: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    qr_token: Optional[str] = None
    dispatched_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    verified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    relief_request: Optional[ReliefRequestOut] = None
    resource: Optional[ResourceOut] = None
    organization: Optional[OrganizationOut] = None
    volunteer: Optional[UserOut] = None
    recipient: Optional[UserOut] = None
