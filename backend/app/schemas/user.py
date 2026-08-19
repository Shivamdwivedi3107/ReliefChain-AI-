from typing import Optional
from datetime import datetime
from pydantic import EmailStr, Field
from app.schemas.common import BaseSchema
from app.schemas.organization import OrganizationOut


class UserBase(BaseSchema):
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=120)
    role: str = Field(default="citizen")  # citizen, ngo, volunteer, admin
    phone_number: Optional[str] = None
    organization_id: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=100)


class UserUpdate(BaseSchema):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    organization_id: Optional[str] = None


class UserOut(UserBase):
    id: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    organization: Optional[OrganizationOut] = None
