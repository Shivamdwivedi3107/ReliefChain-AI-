from typing import Optional
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema


class NotificationBase(BaseSchema):
    title: str = Field(..., min_length=2, max_length=150)
    message: str = Field(..., min_length=2, max_length=500)
    notification_type: str = Field(default="status_update")
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class NotificationCreate(NotificationBase):
    user_id: str


class NotificationOut(NotificationBase):
    id: str
    user_id: str
    is_read: bool
    created_at: datetime
