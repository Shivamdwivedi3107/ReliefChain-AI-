from typing import Optional
from datetime import datetime
from pydantic import Field
from app.schemas.common import BaseSchema


class QRGenerateRequest(BaseSchema):
    distribution_id: str


class QRGenerateResponse(BaseSchema):
    distribution_id: str
    verification_token: str
    qr_code_image_base64: str
    verification_url: str
    expires_at: Optional[datetime] = None


class QRVerifyRequest(BaseSchema):
    verification_token: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class QRVerifyResponse(BaseSchema):
    status: str  # valid, already_verified, invalid, expired
    is_valid: bool
    distribution_id: Optional[str] = None
    recipient_name: Optional[str] = None
    resource_name: Optional[str] = None
    quantity: Optional[float] = None
    verified_at: Optional[datetime] = None
    blockchain_tx_hash: Optional[str] = None
