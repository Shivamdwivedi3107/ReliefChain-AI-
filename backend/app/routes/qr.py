import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.qr_verification import QRVerification
from app.models.distribution import Distribution
from app.models.resource import ResourceInventory
from app.models.relief_request import ReliefRequest
from app.models.notification import Notification
from app.models.user import User
from app.models.blockchain import BlockchainTransaction
from app.schemas.qr import (
    QRGenerateRequest,
    QRGenerateResponse,
    QRVerifyRequest,
    QRVerifyResponse,
)
from app.services.qr_service import generate_qr_base64_image
from app.services.blockchain_service import blockchain_service

router = APIRouter(prefix="/qr", tags=["QR Verification & Proof of Delivery"])


@router.post("/generate/{distribution_id}", response_model=QRGenerateResponse, summary="Generate dynamic QR verification token for distribution")
def generate_distribution_qr(
    distribution_id: str,
    db: Session = Depends(get_db),
):
    dist = db.query(Distribution).filter(Distribution.id == distribution_id).first()
    if not dist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distribution record not found")

    # Reuse existing valid token or generate new one
    qr_ver = (
        db.query(QRVerification)
        .filter(
            QRVerification.distribution_id == distribution_id,
            QRVerification.status == "valid",
        )
        .first()
    )

    if not qr_ver:
        token = secrets.token_urlsafe(32)
        dist.qr_token = token
        qr_ver = QRVerification(
            distribution_id=distribution_id,
            verification_token=token,
            status="valid",
            expires_at=datetime.now(timezone.utc) + timedelta(days=3),
        )
        db.add(qr_ver)
    else:
        token = qr_ver.verification_token

    # Verification URL representation
    verification_url = f"/api/v1/qr/verify/{token}"
    qr_img = generate_qr_base64_image(token)
    qr_ver.qr_code_data = qr_img

    db.commit()

    return QRGenerateResponse(
        distribution_id=dist.id,
        verification_token=token,
        qr_code_image_base64=qr_img,
        verification_url=verification_url,
        expires_at=qr_ver.expires_at,
    )


@router.get("/verify/{token}", response_model=QRVerifyResponse, summary="Verify QR verification token")
def verify_token_get(
    token: str,
    db: Session = Depends(get_db),
):
    qr_ver = db.query(QRVerification).filter(QRVerification.verification_token == token).first()
    if not qr_ver:
        return QRVerifyResponse(
            status="invalid",
            is_valid=False,
        )

    if qr_ver.status == "verified":
        return QRVerifyResponse(
            status="already_verified",
            is_valid=False,
            distribution_id=qr_ver.distribution_id,
            verified_at=qr_ver.verified_at,
        )

    dist = qr_ver.distribution
    recipient_name = dist.recipient.full_name if dist and dist.recipient else "Citizen Recipient"
    resource_name = dist.resource.name if dist and dist.resource else "Relief Item"
    qty = dist.quantity if dist else 1.0

    return QRVerifyResponse(
        status="valid",
        is_valid=True,
        distribution_id=qr_ver.distribution_id,
        recipient_name=recipient_name,
        resource_name=resource_name,
        quantity=qty,
    )


@router.post(
    "/confirm",
    response_model=QRVerifyResponse,
    dependencies=[Depends(rate_limit_dependency(max_requests=settings.RATE_LIMIT_QR_PER_MINUTE, window_seconds=60))],
    summary="Field Volunteer confirms delivery via QR scan and GPS coordinates",
)
def confirm_delivery_qr(
    payload: QRVerifyRequest,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    qr_ver = db.query(QRVerification).filter(QRVerification.verification_token == payload.verification_token).first()
    if not qr_ver:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid verification token")

    if qr_ver.status == "verified":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="This QR verification token has already been redeemed.")

    dist = qr_ver.distribution
    if not dist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Linked distribution not found")

    now = datetime.now(timezone.utc)
    qr_ver.status = "verified"
    qr_ver.verified_at = now
    qr_ver.verified_by_user_id = current_user.id
    qr_ver.verification_lat = payload.latitude
    qr_ver.verification_lng = payload.longitude

    # Update distribution status
    dist.status = "verified"
    dist.verified_at = now

    # Finalize warehouse inventory reduction
    inv = (
        db.query(ResourceInventory)
        .filter(
            ResourceInventory.organization_id == dist.organization_id,
            ResourceInventory.resource_id == dist.resource_id,
        )
        .first()
    )
    if inv:
        inv.reserved_quantity = max(0.0, inv.reserved_quantity - dist.quantity)
        inv.total_quantity = max(0.0, inv.total_quantity - dist.quantity)

    # Update relief request if all items delivered
    req = dist.relief_request
    if req:
        req.status = "completed"

    # Commit verification hash to blockchain ledger
    latest_tx = db.query(BlockchainTransaction).order_by(BlockchainTransaction.created_at.desc()).first()
    prev_hash = latest_tx.current_hash if latest_tx else "0000000000000000000000000000000000000000000000000000000000000000"
    tx_hash, block_num, tx_status = blockchain_service.record_hash_on_chain(
        record_hash=dist.record_hash or "hash_dist_proof",
        event_type="qr_verification",
        reference_id=dist.id,
        previous_hash=prev_hash,
    )
    dist.blockchain_tx_hash = tx_hash

    bc_tx = BlockchainTransaction(
        event_type="qr_verification",
        reference_id=dist.id,
        record_hash=dist.record_hash or "hash_dist_proof",
        previous_hash=prev_hash,
        tx_hash=tx_hash,
        block_number=block_num,
        status=tx_status,
    )
    db.add(bc_tx)

    # Notify Citizen
    if dist.recipient_id:
        notif = Notification(
            user_id=dist.recipient_id,
            title="Relief Delivery Successfully Verified",
            message="Your relief package handover has been cryptographically verified on-chain. Thank you!",
            notification_type="verification",
            reference_id=dist.id,
            reference_type="distribution",
        )
        db.add(notif)

    db.commit()
    db.refresh(dist)

    return QRVerifyResponse(
        status="verified",
        is_valid=True,
        distribution_id=dist.id,
        recipient_name=dist.recipient.full_name if dist.recipient else "Citizen",
        resource_name=dist.resource.name if dist.resource else "Relief Item",
        quantity=dist.quantity,
        verified_at=now,
        blockchain_tx_hash=tx_hash,
    )
