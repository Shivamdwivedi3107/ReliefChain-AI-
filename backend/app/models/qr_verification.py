from sqlalchemy import Column, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid


class QRVerification(Base, TimestampMixin):
    __tablename__ = "qr_verifications"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    distribution_id = Column(String(36), ForeignKey("distributions.id", ondelete="CASCADE"), nullable=False, index=True)
    verification_token = Column(String(128), nullable=False, unique=True, index=True)
    qr_code_data = Column(Text, nullable=True)  # Payload or Base64 QR
    status = Column(String(30), nullable=False, default="valid", index=True)  # valid, verified, expired, revoked

    expires_at = Column(DateTime(timezone=True), nullable=True)
    verified_at = Column(DateTime(timezone=True), nullable=True)
    verified_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)

    verification_lat = Column(Float, nullable=True)
    verification_lng = Column(Float, nullable=True)

    # Relationships
    distribution = relationship("Distribution", back_populates="qr_verifications")
    verified_by_user = relationship("User")
