from sqlalchemy import Column, String, JSON, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, get_utc_now


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)  # user_register, mission_assign, mission_status_change, inventory_update, etc.
    entity_type = Column(String(50), nullable=False, index=True)  # user, relief_request, distribution, inventory, donation, etc.
    entity_id = Column(String(36), nullable=True, index=True)
    details_json = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
