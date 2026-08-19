from sqlalchemy import Column, String, Float, Text, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Disaster(Base, TimestampMixin):
    __tablename__ = "disasters"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    title = Column(String(150), nullable=False, index=True)
    disaster_type = Column(String(50), nullable=False, index=True)  # flood, earthquake, cyclone, wildfire, landslide, other
    severity = Column(String(30), nullable=False, default="medium", index=True)  # low, medium, high, critical
    status = Column(String(30), nullable=False, default="active", index=True)  # active, monitoring, resolved
    location_name = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius_km = Column(Float, nullable=False, default=10.0)
    description = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    resolved_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    relief_requests = relationship("ReliefRequest", back_populates="disaster")
