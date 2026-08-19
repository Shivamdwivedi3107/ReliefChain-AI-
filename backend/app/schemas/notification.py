from typing import Optional, List
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema


class NotificationBase(BaseSchema):
    title: str = Field(..., min_length=2, max_length=150)
    message: str = Field(..., min_length=2, max_length=500)
    notification_type: str = Field(default="system_alert")
    category: str = Field(default="SYSTEM")  # EMERGENCY, MISSION, INVENTORY, DONATION, SECURITY, SYSTEM
    priority: str = Field(default="MEDIUM")  # LOW, MEDIUM, HIGH, CRITICAL
    severity: str = Field(default="info")    # info, warning, critical, success
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None


class NotificationCreate(NotificationBase):
    user_id: str


class NotificationOut(NotificationBase):
    id: str
    user_id: str
    is_read: bool
    is_archived: bool = False
    created_at: datetime


class NotificationUnreadCount(BaseSchema):
    user_id: str
    unread_count: int


class NotificationBulkReadResponse(BaseSchema):
    marked_read_count: int
    success: bool = True
