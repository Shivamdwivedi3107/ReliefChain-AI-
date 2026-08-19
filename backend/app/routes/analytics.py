from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.database import get_db
from app.models.relief_request import ReliefRequest
from app.models.donation import Donation
from app.models.distribution import Distribution
from app.models.organization import Organization
from app.models.disaster import Disaster
from app.models.blockchain import BlockchainTransaction
from app.models.resource import Resource

router = APIRouter(prefix="/analytics", tags=["Analytics & Operational Reports"])


@router.get("/overview", summary="High-level platform KPI analytics overview")
def get_analytics_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_reqs = db.query(func.count(ReliefRequest.id)).scalar() or 0
    completed_reqs = db.query(func.count(ReliefRequest.id)).filter(ReliefRequest.status == "completed").scalar() or 0
    pending_reqs = db.query(func.count(ReliefRequest.id)).filter(ReliefRequest.status == "pending").scalar() or 0

    total_donations_amount = db.query(func.sum(Donation.amount)).filter(Donation.donation_type == "monetary").scalar() or 0.0
    total_dists = db.query(func.count(Distribution.id)).scalar() or 0
    verified_dists = db.query(func.count(Distribution.id)).filter(Distribution.status == "verified").scalar() or 0
    total_bc_records = db.query(func.count(BlockchainTransaction.id)).scalar() or 0

    verification_rate = round((verified_dists / total_dists * 100), 1) if total_dists > 0 else 100.0

    return {
        "kpi": {
            "total_requests": total_reqs,
            "completed_requests": completed_reqs,
            "pending_requests": pending_reqs,
            "total_donations_usd": round(total_donations_amount, 2),
            "total_distributions": total_dists,
            "verified_distributions": verified_dists,
            "delivery_verification_rate_pct": verification_rate,
            "blockchain_audit_proofs": total_bc_records,
        }
    }


@router.get("/disasters-breakdown", summary="Requests aggregated by disaster type")
def get_disaster_breakdown(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    rows = (
        db.query(ReliefRequest.disaster_type, func.count(ReliefRequest.id).label("count"))
        .group_by(ReliefRequest.disaster_type)
        .order_by(desc("count"))
        .all()
    )
    return [{"disaster_type": r[0], "count": r[1]} for r in rows]


@router.get("/priority-breakdown", summary="Requests aggregated by priority classification")
def get_priority_breakdown(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    rows = (
        db.query(ReliefRequest.priority, func.count(ReliefRequest.id).label("count"))
        .group_by(ReliefRequest.priority)
        .order_by(desc("count"))
        .all()
    )
    return [{"priority": r[0], "count": r[1]} for r in rows]


@router.get("/ngo-performance", summary="NGO relief fulfillment metrics")
def get_ngo_performance(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    orgs = db.query(Organization).all()
    results = []
    for org in orgs:
        assigned = db.query(func.count(ReliefRequest.id)).filter(ReliefRequest.assigned_organization_id == org.id).scalar() or 0
        completed = db.query(func.count(ReliefRequest.id)).filter(ReliefRequest.assigned_organization_id == org.id, ReliefRequest.status == "completed").scalar() or 0
        distributions = db.query(func.count(Distribution.id)).filter(Distribution.organization_id == org.id).scalar() or 0
        verified = db.query(func.count(Distribution.id)).filter(Distribution.organization_id == org.id, Distribution.status == "verified").scalar() or 0
        
        results.append({
            "organization_id": org.id,
            "name": org.name,
            "status": org.verification_status,
            "assigned_requests": assigned,
            "completed_requests": completed,
            "total_distributions": distributions,
            "verified_distributions": verified,
        })
    return results
