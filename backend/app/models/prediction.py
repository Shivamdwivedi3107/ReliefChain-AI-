from sqlalchemy import Column, String, Integer, Float, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import generate_uuid, get_utc_now


class PredictionHistory(Base):
    __tablename__ = "prediction_histories"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    request_id = Column(String(36), ForeignKey("relief_requests.id", ondelete="SET NULL"), nullable=True, index=True)
    disaster_type = Column(String(50), nullable=False)
    affected_people = Column(Integer, nullable=False)
    location_risk_score = Column(Float, nullable=False, default=1.0)
    medical_needed = Column(Integer, nullable=False, default=0)
    food_needed = Column(Integer, nullable=False, default=0)
    water_needed = Column(Integer, nullable=False, default=0)
    vulnerable_population = Column(Integer, nullable=False, default=0)

    predicted_priority = Column(String(30), nullable=False, index=True)  # low, medium, high, critical
    confidence_score = Column(Float, nullable=False)
    contributing_factors = Column(JSON, nullable=True)
    model_version = Column(String(50), default="1.0.0")
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False, index=True)

    # Relationships
    relief_request = relationship("ReliefRequest", back_populates="prediction_records")
