from typing import Optional, Dict, Any
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema


class AuditLogOut(BaseSchema):
    id: str
    user_id: Optional[str] = None
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    details_json: Optional[Dict[str, Any]] = None
    ip_address: Optional[str] = None
    created_at: datetime
