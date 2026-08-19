from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Organization(Base, TimestampMixin):
    __tablename__ = "organizations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    name = Column(String(150), nullable=False, unique=True, index=True)
    registration_number = Column(String(100), nullable=False, unique=True, index=True)
    organization_type = Column(String(50), nullable=False, default="NGO")  # NGO, Government, RedCross, Private
    contact_email = Column(String(120), nullable=False, unique=True, index=True)
    contact_phone = Column(String(30), nullable=False)
    address = Column(Text, nullable=True)
    wallet_address = Column(String(64), nullable=True)  # Ethereum address for audit sign-offs
    verification_status = Column(String(30), nullable=False, default="pending", index=True)  # pending, verified, suspended
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    members = relationship("User", back_populates="organization", cascade="all, delete-orphan")
    inventories = relationship("ResourceInventory", back_populates="organization", cascade="all, delete-orphan")
    donations_received = relationship("Donation", back_populates="organization")
    distributions = relationship("Distribution", back_populates="organization")
    assigned_requests = relationship("ReliefRequest", back_populates="assigned_organization")
