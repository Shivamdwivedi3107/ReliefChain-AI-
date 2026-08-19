from typing import Optional
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema
from app.schemas.organization import OrganizationOut


class ResourceBase(BaseSchema):
    name: str = Field(..., min_length=2, max_length=120)
    category: str = Field(..., min_length=2, max_length=50)
    unit: str = Field(default="units")
    description: Optional[str] = None


class ResourceCreate(ResourceBase):
    pass


class ResourceUpdate(BaseSchema):
    name: Optional[str] = None
    category: Optional[str] = None
    unit: Optional[str] = None
    description: Optional[str] = None


class ResourceOut(ResourceBase):
    id: str
    created_at: datetime
    updated_at: datetime


class InventoryCreate(BaseSchema):
    resource_id: str
    quantity: float = Field(..., gt=0)
    warehouse_location: Optional[str] = None


class InventoryUpdate(BaseSchema):
    total_quantity: Optional[float] = None
    available_quantity: Optional[float] = None
    reserved_quantity: Optional[float] = None
    warehouse_location: Optional[str] = None


class InventoryOut(BaseSchema):
    id: str
    organization_id: str
    resource_id: str
    total_quantity: float
    available_quantity: float
    reserved_quantity: float
    warehouse_location: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resource: Optional[ResourceOut] = None
    organization: Optional[OrganizationOut] = None
