import hashlib
import json
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.donation import Donation
from app.models.organization import Organization
from app.models.resource import Resource, ResourceInventory
from app.models.blockchain import BlockchainTransaction
from app.models.user import User
from app.services.blockchain_service import blockchain_service
from app.schemas.donation import (
    DonationCreate,
    DonationUpdate,
    DonationOut,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/donations", tags=["Donations & Public Transparency"])


def generate_donation_record_hash(donation: Donation) -> str:
    """Generate canonical SHA-256 fingerprint for donation record."""
    canonical_payload = {
        "id": donation.id,
        "donor_name": donation.donor_name,
        "donation_type": donation.donation_type,
        "amount": donation.amount,
        "currency": donation.currency,
        "resource_id": donation.resource_id,
        "quantity": donation.quantity,
        "organization_id": donation.organization_id,
        "status": donation.status,
    }
    encoded = json.dumps(canonical_payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@router.post("", response_model=DonationOut, status_code=status.HTTP_201_CREATED, summary="Create a monetary or in-kind resource donation")
def create_donation(
    payload: DonationCreate,
    db: Session = Depends(get_db),
):
    # Validate organization
    org = db.query(Organization).filter(Organization.id == payload.organization_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Target organization not found")

    # If physical resource, validate resource ID
    if payload.donation_type == "resource":
        if not payload.resource_id or not payload.quantity or payload.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Resource donations require a valid resource_id and positive quantity.",
            )
        res = db.query(Resource).filter(Resource.id == payload.resource_id).first()
        if not res:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource item not found")

    donation = Donation(
        donor_id=payload.donor_id,
        donor_name=payload.donor_name,
        donor_email=payload.donor_email,
        donation_type=payload.donation_type,
        currency=payload.currency,
        amount=payload.amount,
        resource_id=payload.resource_id,
        quantity=payload.quantity,
        organization_id=payload.organization_id,
        status="received",
        notes=payload.notes,
    )
    db.add(donation)
    db.commit()
    db.refresh(donation)

    # Compute SHA-256 cryptographic record hash
    rec_hash = generate_donation_record_hash(donation)
    setattr(donation, "record_hash", rec_hash)

    # Link to transparency ledger / blockchain
    latest_tx = db.query(BlockchainTransaction).order_by(BlockchainTransaction.created_at.desc()).first()
    prev_hash = latest_tx.current_hash if latest_tx else "0000000000000000000000000000000000000000000000000000000000000000"
    tx_hash, block_num, tx_status = blockchain_service.record_hash_on_chain(
        record_hash=rec_hash,
        event_type="donation",
        reference_id=str(donation.id),
        previous_hash=prev_hash,
    )
    setattr(donation, "blockchain_tx_hash", tx_hash)

    bc_tx = BlockchainTransaction(
        event_type="donation",
        reference_id=str(donation.id),
        record_hash=rec_hash,
        previous_hash=prev_hash,
        tx_hash=tx_hash,
        block_number=block_num,
        status=tx_status,
    )
    db.add(bc_tx)

    # If resource donation, automatically increment NGO inventory
    if donation.donation_type == "resource" and donation.resource_id and donation.quantity:
        inv = (
            db.query(ResourceInventory)
            .filter(
                ResourceInventory.organization_id == donation.organization_id,
                ResourceInventory.resource_id == donation.resource_id,
            )
            .first()
        )
        if inv:
            inv.total_quantity += donation.quantity
            inv.available_quantity += donation.quantity
        else:
            inv = ResourceInventory(
                organization_id=donation.organization_id,
                resource_id=donation.resource_id,
                total_quantity=donation.quantity,
                available_quantity=donation.quantity,
                reserved_quantity=0.0,
                warehouse_location="Main Relief Depot",
            )
            db.add(inv)

    db.commit()
    db.refresh(donation)
    return donation


@router.get("", response_model=PaginatedResponse[DonationOut], summary="List donations with public transparency filters")
def list_donations(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    organization_id: Optional[str] = Query(None),
    donation_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Donation)
    if organization_id:
        query = query.filter(Donation.organization_id == organization_id)
    if donation_type:
        query = query.filter(Donation.donation_type == donation_type)
    if status:
        query = query.filter(Donation.status == status)

    total = query.count()
    donations = (
        query.order_by(Donation.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        data=donations,
    )


@router.get("/{donation_id}", response_model=DonationOut, summary="Get donation record by ID")
def get_donation_by_id(donation_id: str, db: Session = Depends(get_db)):
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")
    return donation


@router.patch("/{donation_id}", response_model=DonationOut, summary="Update donation lifecycle status")
def update_donation(
    donation_id: str,
    payload: DonationUpdate,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    donation = db.query(Donation).filter(Donation.id == donation_id).first()
    if not donation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Donation not found")

    if current_user.role != "admin" and current_user.organization_id != donation.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this donation")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(donation, k, v)

    # Re-calculate hash on state update
    rec_hash = generate_donation_record_hash(donation)
    setattr(donation, "record_hash", rec_hash)
    db.commit()
    db.refresh(donation)
    return donation
