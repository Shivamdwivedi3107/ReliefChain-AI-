from sqlalchemy import Column, String, Boolean, Float, Integer, JSON, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    email = Column(String(120), unique=True, nullable=False, index=True)
    full_name = Column(String(120), nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, default="citizen", index=True)  # citizen, ngo, volunteer, admin, donor
    phone_number = Column(String(30), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)

    # Volunteer Profile & Dynamic Dispatch Metrics
    availability = Column(Boolean, default=True, nullable=False)
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    skills = Column(JSON, default=list, nullable=True)  # e.g. ["medical", "rescue", "logistics", "first_aid"]
    max_mission_capacity = Column(Integer, default=3, nullable=False)
    reliability_score = Column(Float, default=95.0, nullable=False)  # 0.0 to 100.0

    # Optional linkage to NGO / Relief Organization
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    organization = relationship("Organization", back_populates="members")
    relief_requests = relationship("ReliefRequest", foreign_keys="ReliefRequest.citizen_id", back_populates="citizen")
    assigned_volunteer_requests = relationship("ReliefRequest", foreign_keys="ReliefRequest.assigned_volunteer_id", back_populates="assigned_volunteer")
    donations = relationship("Donation", back_populates="donor")
    volunteer_distributions = relationship("Distribution", foreign_keys="Distribution.volunteer_id", back_populates="volunteer")
    notifications = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
