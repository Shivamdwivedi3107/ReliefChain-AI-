from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, get_utc_now


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(150), nullable=False)
    message = Column(String(500), nullable=False)
    
    # Priority & Category Taxonomy
    notification_type = Column(String(50), nullable=False, default="system_alert", index=True)  # legacy compatibility
    category = Column(String(50), nullable=False, default="SYSTEM", index=True)  # EMERGENCY, MISSION, INVENTORY, DONATION, SECURITY, SYSTEM
    priority = Column(String(30), nullable=False, default="MEDIUM", index=True)  # LOW, MEDIUM, HIGH, CRITICAL
    severity = Column(String(30), nullable=False, default="info")  # info, warning, critical, success
    
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    is_archived = Column(Boolean, default=False, nullable=False, index=True)
    
    reference_id = Column(String(36), nullable=True)
    reference_type = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="notifications")
