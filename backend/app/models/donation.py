from sqlalchemy import Column, String, Float, Text, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class Donation(Base, TimestampMixin):
    __tablename__ = "donations"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    donor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    donor_name = Column(String(120), nullable=False)
    donor_email = Column(String(120), nullable=True)
    donation_type = Column(String(30), nullable=False, default="monetary", index=True)  # monetary, resource
    currency = Column(String(10), default="USD")
    amount = Column(Float, nullable=True)  # For monetary donations

    # Resource donation specifics
    resource_id = Column(String(36), ForeignKey("resources.id", ondelete="SET NULL"), nullable=True, index=True)
    quantity = Column(Float, nullable=True)

    # Destination NGO
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="RESTRICT"), nullable=False, index=True)

    status = Column(String(30), nullable=False, default="received", index=True)  # pending, received, allocated, distributed
    transaction_reference = Column(String(100), nullable=True, index=True)
    record_hash = Column(String(64), nullable=True, index=True)  # SHA-256 state hash committed to blockchain
    blockchain_tx_hash = Column(String(66), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    donor = relationship("User", back_populates="donations")
    organization = relationship("Organization", back_populates="donations_received")
    resource = relationship("Resource", back_populates="donations")
