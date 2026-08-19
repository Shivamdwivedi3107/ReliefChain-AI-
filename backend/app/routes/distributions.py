import hashlib
import json
import secrets
from datetime import datetime, timezone
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.distribution import Distribution
from app.models.relief_request import ReliefRequest
from app.models.resource import Resource, ResourceInventory
from app.models.user import User
from app.models.notification import Notification
from app.models.qr_verification import QRVerification
from app.models.blockchain import BlockchainTransaction
from app.services.blockchain_service import blockchain_service
from app.schemas.distribution import (
    DistributionCreate,
    DistributionUpdate,
    DistributionOut,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/distributions", tags=["Relief Distributions"])


def generate_distribution_record_hash(dist: Distribution) -> str:
    """Generate canonical SHA-256 state fingerprint for distribution record."""
    canonical_payload = {
        "id": dist.id,
        "relief_request_id": dist.relief_request_id,
        "resource_id": dist.resource_id,
        "quantity": dist.quantity,
        "organization_id": dist.organization_id,
        "volunteer_id": dist.volunteer_id,
        "recipient_id": dist.recipient_id,
        "status": dist.status,
    }
    encoded = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@router.post("", response_model=DistributionOut, status_code=status.HTTP_201_CREATED, summary="Create and dispatch a relief distribution mission")
def create_distribution(
    payload: DistributionCreate,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    # Validate Relief Request
    req = db.query(ReliefRequest).filter(ReliefRequest.id == payload.relief_request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relief request not found")

    # Validate Organization Inventory
    inv = (
        db.query(ResourceInventory)
        .filter(
            ResourceInventory.organization_id == payload.organization_id,
            ResourceInventory.resource_id == payload.resource_id,
        )
        .first()
    )
    if not inv or inv.available_quantity < payload.quantity:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insufficient inventory. Available: {inv.available_quantity if inv else 0}, Requested: {payload.quantity}",
        )

    # Reserve inventory (decrement available, increment reserved)
    inv.available_quantity -= payload.quantity
    inv.reserved_quantity += payload.quantity

    # Generate secure single-use QR verification token
    crypto_token = secrets.token_urlsafe(32)

    distribution = Distribution(
        relief_request_id=payload.relief_request_id,
        resource_id=payload.resource_id,
        organization_id=payload.organization_id,
        volunteer_id=payload.volunteer_id,
        recipient_id=req.citizen_id,
        quantity=payload.quantity,
        status="dispatched",
        dispatch_location=payload.dispatch_location,
        delivery_latitude=payload.delivery_latitude or req.latitude,
        delivery_longitude=payload.delivery_longitude or req.longitude,
        qr_token=crypto_token,
        dispatched_at=datetime.now(timezone.utc),
    )
    db.add(distribution)
    db.commit()
    db.refresh(distribution)

    # Compute Record Hash
    distribution.record_hash = generate_distribution_record_hash(distribution)

    latest_tx = db.query(BlockchainTransaction).order_by(BlockchainTransaction.created_at.desc()).first()
    prev_hash = latest_tx.current_hash if latest_tx else "0000000000000000000000000000000000000000000000000000000000000000"
    tx_hash, block_num, tx_status = blockchain_service.record_hash_on_chain(
        record_hash=distribution.record_hash,
        event_type="distribution",
        reference_id=distribution.id,
        previous_hash=prev_hash,
    )
    distribution.blockchain_tx_hash = tx_hash

    bc_tx = BlockchainTransaction(
        event_type="distribution",
        reference_id=distribution.id,
        record_hash=distribution.record_hash,
        previous_hash=prev_hash,
        tx_hash=tx_hash,
        block_number=block_num,
        status=tx_status,
    )
    db.add(bc_tx)

    # Create associated QR verification entry
    qr_ver = QRVerification(
        distribution_id=distribution.id,
        verification_token=crypto_token,
        status="valid",
    )
    db.add(qr_ver)

    # Update relief request status
    req.status = "in_progress"

    # Notify Citizen
    notif_cit = Notification(
        user_id=req.citizen_id,
        title="Relief Package Dispatched!",
        message=f"A relief package with quantity {payload.quantity} is on its way. Ready your verification QR code.",
        notification_type="status_update",
        reference_id=distribution.id,
        reference_type="distribution",
    )
    db.add(notif_cit)

    # Notify Volunteer if assigned
    if payload.volunteer_id:
        notif_vol = Notification(
            user_id=payload.volunteer_id,
            title="Distribution Mission Dispatched",
            message=f"Mission active: Deliver items to {req.location_name}.",
            notification_type="assignment",
            reference_id=distribution.id,
            reference_type="distribution",
        )
        db.add(notif_vol)

    db.commit()
    db.refresh(distribution)
    return distribution


@router.get("", response_model=PaginatedResponse[DistributionOut], summary="List distributions with pagination and filters")
def list_distributions(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    organization_id: Optional[str] = Query(None),
    volunteer_id: Optional[str] = Query(None),
    recipient_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Distribution)
    if organization_id:
        query = query.filter(Distribution.organization_id == organization_id)
    if volunteer_id:
        query = query.filter(Distribution.volunteer_id == volunteer_id)
    if recipient_id:
        query = query.filter(Distribution.recipient_id == recipient_id)
    if status:
        query = query.filter(Distribution.status == status)

    total = query.count()
    items = (
        query.order_by(Distribution.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        data=items,
    )


@router.get("/{distribution_id}", response_model=DistributionOut, summary="Get distribution mission details by ID")
def get_distribution_by_id(distribution_id: str, db: Session = Depends(get_db)):
    dist = db.query(Distribution).filter(Distribution.id == distribution_id).first()
    if not dist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distribution not found")
    return dist


@router.patch("/{distribution_id}", response_model=DistributionOut, summary="Update distribution mission status")
def update_distribution(
    distribution_id: str,
    payload: DistributionUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    dist = db.query(Distribution).filter(Distribution.id == distribution_id).first()
    if not dist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Distribution not found")

    update_dict = payload.model_dump(exclude_unset=True)

    # Handle completion / verification inventory updates
    if "status" in update_dict:
        new_status = update_dict["status"]
        if new_status in ["delivered", "verified"] and dist.status not in ["delivered", "verified"]:
            # Finalize inventory deduction
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

            if new_status == "delivered":
                dist.delivered_at = datetime.now(timezone.utc)
            elif new_status == "verified":
                dist.verified_at = datetime.now(timezone.utc)

        elif new_status == "cancelled" and dist.status != "cancelled":
            # Revert reserved inventory back to available
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
                inv.available_quantity += dist.quantity

    for k, v in update_dict.items():
        setattr(dist, k, v)

    dist.record_hash = generate_distribution_record_hash(dist)
    db.commit()
    db.refresh(dist)
    return dist
