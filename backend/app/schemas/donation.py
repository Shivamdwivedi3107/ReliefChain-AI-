from typing import Optional
from datetime import datetime
from pydantic import Field, EmailStr
from app.schemas.common import BaseSchema
from app.schemas.user import UserOut
from app.schemas.organization import OrganizationOut
from app.schemas.resource import ResourceOut


class DonationBase(BaseSchema):
    donor_name: str = Field(..., min_length=2, max_length=120)
    donor_email: Optional[EmailStr] = None
    donation_type: str = Field(default="monetary")  # monetary, resource
    currency: str = Field(default="USD")
    amount: Optional[float] = None
    resource_id: Optional[str] = None
    quantity: Optional[float] = None
    organization_id: str
    notes: Optional[str] = None


class DonationCreate(DonationBase):
    donor_id: Optional[str] = None


class DonationUpdate(BaseSchema):
    status: Optional[str] = None  # pending, received, allocated, distributed
    transaction_reference: Optional[str] = None
    record_hash: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    notes: Optional[str] = None


class DonationOut(DonationBase):
    id: str
    donor_id: Optional[str] = None
    status: str
    transaction_reference: Optional[str] = None
    record_hash: Optional[str] = None
    blockchain_tx_hash: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    donor: Optional[UserOut] = None
    organization: Optional[OrganizationOut] = None
    resource: Optional[ResourceOut] = None
