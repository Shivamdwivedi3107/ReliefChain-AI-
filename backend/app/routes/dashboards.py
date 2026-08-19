from typing import Dict, Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.user import User
from app.models.organization import Organization
from app.models.disaster import Disaster
from app.models.relief_request import ReliefRequest
from app.models.resource import Resource, ResourceInventory
from app.models.donation import Donation
from app.models.distribution import Distribution
from app.models.blockchain import BlockchainTransaction

router = APIRouter(prefix="/dashboards", tags=["Dashboards & Metrics"])


@router.get("/admin", summary="Comprehensive Admin operational metrics")
def get_admin_dashboard(
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # User counts
    total_users = db.query(func.count(User.id)).scalar()
    users_by_role = dict(
        db.query(User.role, func.count(User.id)).group_by(User.role).all()
    )

    # Organization counts
    total_orgs = db.query(func.count(Organization.id)).scalar()
    orgs_by_status = dict(
        db.query(Organization.verification_status, func.count(Organization.id))
        .group_by(Organization.verification_status)
        .all()
    )

    # Disasters
    active_disasters_count = (
        db.query(func.count(Disaster.id))
        .filter(Disaster.status == "active")
        .scalar()
    )

    # Relief Requests
    total_requests = db.query(func.count(ReliefRequest.id)).scalar()
    requests_by_status = dict(
        db.query(ReliefRequest.status, func.count(ReliefRequest.id))
        .group_by(ReliefRequest.status)
        .all()
    )
    requests_by_priority = dict(
        db.query(ReliefRequest.priority, func.count(ReliefRequest.id))
        .group_by(ReliefRequest.priority)
        .all()
    )

    # Donations
    total_monetary_donations = (
        db.query(func.sum(Donation.amount))
        .filter(Donation.donation_type == "monetary")
        .scalar()
        or 0.0
    )
    total_donation_records = db.query(func.count(Donation.id)).scalar()

    # Distributions
    total_distributions = db.query(func.count(Distribution.id)).scalar()
    distributions_by_status = dict(
        db.query(Distribution.status, func.count(Distribution.id))
        .group_by(Distribution.status)
        .all()
    )

    # Blockchain
    total_blockchain_txs = db.query(func.count(BlockchainTransaction.id)).scalar()

    return {
        "users": {
            "total": total_users,
            "by_role": users_by_role,
        },
        "organizations": {
            "total": total_orgs,
            "by_status": orgs_by_status,
        },
        "disasters": {
            "active_count": active_disasters_count,
        },
        "relief_requests": {
            "total": total_requests,
            "by_status": requests_by_status,
            "by_priority": requests_by_priority,
        },
        "donations": {
            "total_monetary_amount": round(total_monetary_donations, 2),
            "total_records": total_donation_records,
        },
        "distributions": {
            "total": total_distributions,
            "by_status": distributions_by_status,
            "verified_count": distributions_by_status.get("verified", 0),
        },
        "blockchain": {
            "total_transactions": total_blockchain_txs,
        },
    }


@router.get("/ngo/{org_id}", summary="NGO coordinator operational dashboard")
def get_ngo_dashboard(
    org_id: str,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if current_user.role != "admin" and current_user.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this organization")

    # Assigned requests
    assigned_requests = (
        db.query(ReliefRequest)
        .filter(ReliefRequest.assigned_organization_id == org_id)
        .all()
    )
    req_status_counts = {}
    for r in assigned_requests:
        req_status_counts[r.status] = req_status_counts.get(r.status, 0) + 1

    # Inventory balances
    inventories = (
        db.query(ResourceInventory)
        .filter(ResourceInventory.organization_id == org_id)
        .all()
    )
    inventory_summary = [
        {
            "resource_id": inv.resource_id,
            "resource_name": inv.resource.name if inv.resource else "Item",
            "category": inv.resource.category if inv.resource else "General",
            "unit": inv.resource.unit if inv.resource else "units",
            "total": inv.total_quantity,
            "available": inv.available_quantity,
            "reserved": inv.reserved_quantity,
            "warehouse": inv.warehouse_location,
        }
        for inv in inventories
    ]

    # Distributions
    distributions = (
        db.query(Distribution)
        .filter(Distribution.organization_id == org_id)
        .all()
    )
    dist_status_counts = {}
    for d in distributions:
        dist_status_counts[d.status] = dist_status_counts.get(d.status, 0) + 1

    # Volunteers
    volunteers_count = (
        db.query(func.count(User.id))
        .filter(User.organization_id == org_id, User.role == "volunteer")
        .scalar()
    )

    return {
        "organization": {
            "id": org.id,
            "name": org.name,
            "status": org.verification_status,
            "wallet_address": org.wallet_address,
        },
        "requests": {
            "total_assigned": len(assigned_requests),
            "by_status": req_status_counts,
        },
        "inventory": inventory_summary,
        "distributions": {
            "total": len(distributions),
            "by_status": dist_status_counts,
        },
        "volunteers_count": volunteers_count,
    }


@router.get("/citizen", summary="Citizen personal dashboard")
def get_citizen_dashboard(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # My requests
    requests = (
        db.query(ReliefRequest)
        .filter(ReliefRequest.citizen_id == current_user.id)
        .order_by(ReliefRequest.created_at.desc())
        .all()
    )

    req_by_status = {}
    for r in requests:
        req_by_status[r.status] = req_by_status.get(r.status, 0) + 1

    # Active disasters
    active_disasters = (
        db.query(Disaster)
        .filter(Disaster.status == "active")
        .order_by(Disaster.created_at.desc())
        .limit(5)
        .all()
    )

    # My donations
    donations = (
        db.query(Donation)
        .filter(Donation.donor_id == current_user.id)
        .order_by(Donation.created_at.desc())
        .all()
    )

    return {
        "my_requests": {
            "total": len(requests),
            "by_status": req_by_status,
            "recent": [
                {
                    "id": r.id,
                    "disaster_type": r.disaster_type,
                    "location_name": r.location_name,
                    "priority": r.priority,
                    "status": r.status,
                    "created_at": r.created_at,
                }
                for r in requests[:5]
            ],
        },
        "active_disasters": [
            {
                "id": d.id,
                "title": d.title,
                "type": d.disaster_type,
                "severity": d.severity,
                "location": d.location_name,
                "latitude": d.latitude,
                "longitude": d.longitude,
            }
            for d in active_disasters
        ],
        "my_donations": [
            {
                "id": don.id,
                "type": don.donation_type,
                "amount": don.amount,
                "currency": don.currency,
                "status": don.status,
                "record_hash": don.record_hash,
                "blockchain_tx_hash": don.blockchain_tx_hash,
                "created_at": don.created_at,
            }
            for don in donations
        ],
    }
