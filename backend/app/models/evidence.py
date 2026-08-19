from sqlalchemy import Column, String, Integer, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid, get_utc_now


class Evidence(Base, TimestampMixin):
    __tablename__ = "evidence_records"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    uploaded_by = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    
    relief_request_id = Column(String(36), ForeignKey("relief_requests.id", ondelete="CASCADE"), nullable=True, index=True)
    distribution_id = Column(String(36), ForeignKey("distributions.id", ondelete="CASCADE"), nullable=True, index=True)
    
    file_name = Column(String(255), nullable=False)
    stored_name = Column(String(255), nullable=False, unique=True)
    file_path = Column(String(500), nullable=False)
    content_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    description = Column(Text, nullable=True)

    # Relationships
    uploader = relationship("User")
    relief_request = relationship("ReliefRequest")
    distribution = relationship("Distribution")
