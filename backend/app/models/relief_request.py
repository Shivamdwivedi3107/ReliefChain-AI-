from sqlalchemy import Column, String, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class ReliefRequest(Base, TimestampMixin):
    __tablename__ = "relief_requests"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    citizen_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    disaster_id = Column(String(36), ForeignKey("disasters.id", ondelete="SET NULL"), nullable=True, index=True)
    disaster_type = Column(String(50), nullable=False, index=True)
    location_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    affected_people = Column(Integer, nullable=False, default=1)
    required_resources = Column(JSON, nullable=False, default=list)  # List of items or structured categories
    urgency_description = Column(Text, nullable=True)
    image_reference = Column(String(255), nullable=True)

    # Priority & Status
    priority = Column(String(30), nullable=False, default="medium", index=True)  # low, medium, high, critical
    status = Column(String(30), nullable=False, default="pending", index=True)  # pending, under_review, assigned, in_progress, completed, rejected

    # Assignments
    assigned_organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    assigned_volunteer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    # AI Decision Support Metadata
    ai_predicted_priority = Column(String(30), nullable=True)
    ai_confidence = Column(Float, nullable=True)
    ai_factors = Column(JSON, nullable=True)

    # Relationships
    citizen = relationship("User", foreign_keys=[citizen_id], back_populates="relief_requests")
    assigned_volunteer = relationship("User", foreign_keys=[assigned_volunteer_id], back_populates="assigned_volunteer_requests")
    disaster = relationship("Disaster", back_populates="relief_requests")
    assigned_organization = relationship("Organization", back_populates="assigned_requests")
    distributions = relationship("Distribution", back_populates="relief_request", cascade="all, delete-orphan")
    prediction_records = relationship("PredictionHistory", back_populates="relief_request")
