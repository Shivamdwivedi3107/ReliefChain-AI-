from typing import Optional
from datetime import datetime
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema


class OrganizationBase(BaseSchema):
    name: str = Field(..., min_length=2, max_length=150)
    registration_number: str = Field(..., min_length=2, max_length=100)
    organization_type: str = Field(default="NGO")
    contact_email: EmailStr
    contact_phone: str = Field(..., min_length=5, max_length=30)
    address: Optional[str] = None
    wallet_address: Optional[str] = None


class OrganizationCreate(OrganizationBase):
    pass


class OrganizationUpdate(BaseSchema):
    name: Optional[str] = None
    organization_type: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    wallet_address: Optional[str] = None
    verification_status: Optional[str] = None
    is_active: Optional[bool] = None


class OrganizationOut(OrganizationBase):
    id: str
    verification_status: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
