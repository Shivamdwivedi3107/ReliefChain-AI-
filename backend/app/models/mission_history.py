from sqlalchemy import Column, String, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, get_utc_now


class MissionStatusHistory(Base):
    __tablename__ = "mission_status_histories"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    relief_request_id = Column(String(36), ForeignKey("relief_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=False, index=True)
    changed_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    optional_note = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    # Relationships
    relief_request = relationship("ReliefRequest", back_populates="status_history")
    changed_by = relationship("User", foreign_keys=[changed_by_user_id])
