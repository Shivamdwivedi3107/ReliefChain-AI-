from sqlalchemy import Column, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Distribution(Base, TimestampMixin):
    __tablename__ = "distributions"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    relief_request_id = Column(String(36), ForeignKey("relief_requests.id", ondelete="CASCADE"), nullable=False, index=True)
    resource_id = Column(String(36), ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False, index=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)
    volunteer_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    recipient_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    quantity = Column(Float, nullable=False, default=1.0)
    status = Column(String(30), nullable=False, default="scheduled", index=True)  # scheduled, dispatched, delivered, verified, cancelled

    dispatch_location = Column(String(200), nullable=True)
    delivery_latitude = Column(Float, nullable=True)
    delivery_longitude = Column(Float, nullable=True)

    # Verification and Blockchain Audit Hashes
    record_hash = Column(String(64), nullable=True, index=True)  # SHA-256 state hash
    blockchain_tx_hash = Column(String(66), nullable=True)
    qr_token = Column(String(128), nullable=True, unique=True, index=True)

    dispatched_at = Column(DateTime(timezone=True), nullable=True)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    relief_request = relationship("ReliefRequest", back_populates="distributions")
    resource = relationship("Resource", back_populates="distributions")
    organization = relationship("Organization", back_populates="distributions")
    volunteer = relationship("User", foreign_keys=[volunteer_id], back_populates="volunteer_distributions")
    recipient = relationship("User", foreign_keys=[recipient_id])
    qr_verifications = relationship("QRVerification", back_populates="distribution", cascade="all, delete-orphan")
