from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema
from app.schemas.relief_request import ReliefRequestOut


class MissionStatusUpdate(BaseSchema):
    new_status: str = Field(..., description="Target status: triaged, assigned, dispatched, in_progress, delivered, completed, cancelled")
    note: Optional[str] = Field(None, max_length=500, description="Optional transition note or rationale")


class MissionStatusHistoryOut(BaseSchema):
    id: str
    relief_request_id: str
    previous_status: Optional[str] = None
    new_status: str
    changed_by_user_id: Optional[str] = None
    optional_note: Optional[str] = None
    created_at: datetime


class MissionDetailOut(ReliefRequestOut):
    status_history: List[MissionStatusHistoryOut] = []
