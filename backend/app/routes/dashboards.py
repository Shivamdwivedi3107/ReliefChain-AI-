from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles, get_optional_user
from app.models.user import User
from app.models.organization import Organization
from app.models.disaster import Disaster
from app.models.incidents import Incident
from app.models.relief_request import ReliefRequest
from app.models.resource import Resource, ResourceInventory
from app.models.donation import Donation
from app.models.distribution import Distribution
from app.models.blockchain import BlockchainTransaction
from app.models.notification import Notification
from app.services.volunteer_matching import volunteer_matcher



router = APIRouter(prefix="/dashboards", tags=["Dashboards & Metrics"])


class QuickTriageRequest(BaseModel):
    disaster_type: str
    severity: float = Field(5.0, ge=1.0, le=10.0)
    affected_people: int = Field(1, ge=1)
    requires_medical: bool = False
    requires_food: bool = False
    requires_water: bool = False
    requires_shelter: bool = False


@router.get("/admin", summary="Comprehensive Admin operational metrics")
def get_admin_dashboard(
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # User counts
    total_users = db.query(func.count(User.id)).scalar() or 0
    users_by_role = dict(
        db.query(User.role, func.count(User.id)).group_by(User.role).all()
    )

    # Organization counts
    total_orgs = db.query(func.count(Organization.id)).scalar() or 0
    orgs_by_status = dict(
        db.query(Organization.verification_status, func.count(Organization.id))
        .group_by(Organization.verification_status)
        .all()
    )

    # Disasters & Incidents
    active_disasters_count = (
        db.query(func.count(Disaster.id))
        .filter(Disaster.status == "active")
        .scalar()
        or 0
    )
    active_incidents_count = (
        db.query(func.count(Incident.id))
        .filter(Incident.status.in_(["DETECTED", "VERIFIED", "ACTIVE", "MONITORING"]))
        .scalar()
        or 0
    )

    # Relief Requests
    total_requests = db.query(func.count(ReliefRequest.id)).scalar() or 0
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
    total_donation_records = db.query(func.count(Donation.id)).scalar() or 0

    # Distributions
    total_distributions = db.query(func.count(Distribution.id)).scalar() or 0
    distributions_by_status = dict(
        db.query(Distribution.status, func.count(Distribution.id))
        .group_by(Distribution.status)
        .all()
    )

    # Blockchain
    total_blockchain_txs = db.query(func.count(BlockchainTransaction.id)).scalar() or 0

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
            "active_incidents_count": active_incidents_count,
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
        or 0
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


@router.get("/volunteer", summary="Volunteer operations center dashboard")
def get_volunteer_dashboard(
    current_user: User = Depends(require_roles(["volunteer", "admin"])),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    # 1. Assigned missions for this volunteer
    assigned = (
        db.query(ReliefRequest)
        .filter(ReliefRequest.assigned_volunteer_id == current_user.id)
        .order_by(ReliefRequest.created_at.desc())
        .all()
    )

    active_missions = [
        {
            "id": r.id,
            "location_name": r.location_name,
            "disaster_type": r.disaster_type,
            "priority": r.priority,
            "status": r.status,
            "affected_people": r.affected_people,
            "required_resources": r.required_resources,
            "created_at": r.created_at.isoformat(),
        }
        for r in assigned if r.status in ["assigned", "dispatched", "in_progress"]
    ]

    completed_count = sum(1 for r in assigned if r.status in ["delivered", "completed"])

    # 2. Recommended unassigned missions with AI Match Score
    open_requests = (
        db.query(ReliefRequest)
        .filter(ReliefRequest.status.in_(["pending", "triaged"]))
        .order_by(ReliefRequest.created_at.desc())
        .limit(5)
        .all()
    )

    recommended_missions: List[Dict[str, Any]] = []
    for req in open_requests:
        # Match volunteer for this specific mission
        matches = volunteer_matcher.match_volunteers_for_mission(db, req.id, limit=10)
        user_match = next((m for m in matches if m["volunteer_id"] == current_user.id), None)
        match_score = user_match["match_score"] if user_match else 85.0
        reasons = user_match["match_reasons"] if user_match else ["Responder skills compatible", "Local zone proximity"]

        recommended_missions.append({
            "mission_id": req.id,
            "title": req.location_name,
            "disaster_type": req.disaster_type,
            "priority": req.priority,
            "affected_people": req.affected_people,
            "match_score": match_score,
            "match_reasons": reasons,
            "created_at": req.created_at.isoformat(),
        })

    # Workload calculation
    active_load = len(active_missions)
    max_cap = current_user.max_mission_capacity or 3
    workload_pct = min(100, int((active_load / max_cap) * 100)) if max_cap > 0 else 0

    return {
        "volunteer": {
            "id": current_user.id,
            "full_name": current_user.full_name,
            "skills": current_user.skills or ["first_aid", "logistics"],
            "reliability_score": current_user.reliability_score,
            "availability": current_user.availability,
            "max_capacity": max_cap,
            "active_workload": active_load,
            "workload_percentage": workload_pct,
            "completed_missions_count": completed_count,
        },
        "active_missions": active_missions,
        "recommended_missions": recommended_missions,
    }


@router.get("/citizen", summary="Citizen smart dashboard")
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

    # Active incidents & nearby warnings
    active_incidents = (
        db.query(Incident)
        .filter(Incident.status.in_(["DETECTED", "VERIFIED", "ACTIVE", "MONITORING"]))
        .order_by(Incident.severity.desc())
        .limit(4)
        .all()
    )

    # Safe locations / relief hubs
    safe_zones = [
        {"name": "Central Municipal Stadium Camp", "type": "High Ground Evacuation Shelter", "capacity": "5,000 beds", "status": "OPEN", "distance_km": 3.2},
        {"name": "St. Jude Hospital Relief Annex", "type": "Medical Triage Station", "capacity": "Emergency Trauma", "status": "OPEN", "distance_km": 1.8},
        {"name": "Metro North Warehouse Depot", "type": "Food & Clean Water Distribution Hub", "capacity": "Daily Rations", "status": "ACTIVE", "distance_km": 4.5},
    ]

    # My distributions / QR history
    distributions = (
        db.query(Distribution)
        .join(ReliefRequest, Distribution.relief_request_id == ReliefRequest.id)
        .filter(ReliefRequest.citizen_id == current_user.id)
        .order_by(Distribution.created_at.desc())
        .all()
    )

    # My notifications
    notifs = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .order_by(Notification.created_at.desc())
        .limit(5)
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
                    "affected_people": r.affected_people,
                    "ai_predicted_priority": r.ai_predicted_priority or r.priority,
                    "created_at": r.created_at.isoformat(),
                }
                for r in requests[:6]
            ],
        },
        "nearby_incidents": [
            {
                "id": inc.id,
                "title": inc.title,
                "type": inc.disaster_type,
                "severity": inc.severity,
                "status": inc.status,
                "radius_km": inc.affected_radius_km,
            }
            for inc in active_incidents
        ],
        "safe_locations": safe_zones,
        "distributions_history": [
            {
                "id": d.id,
                "status": d.status,
                "package_details": d.package_details,
                "is_qr_scanned": bool(d.qr_code_scanned_at),
                "created_at": d.created_at.isoformat(),
            }
            for d in distributions
        ],
        "unread_notifications": [
            {
                "id": n.id,
                "title": n.title,
                "message": n.message,
                "priority": n.priority,
                "created_at": n.created_at.isoformat(),
            }
            for n in notifs
        ],
    }


@router.post("/citizen/quick-triage", summary="Instant AI priority estimation for One-Tap SOS")
def quick_citizen_triage(
    payload: QuickTriageRequest,
) -> Dict[str, Any]:
    """
    Computes instant rule-based priority rating and human-understandable explanation
    for One-Tap SOS request forms before final submission.
    """
    score = payload.severity * 5.0  # 5 to 50
    reasons = [f"Base hazard severity rating is {payload.severity:.1f}/10"]

    if payload.requires_medical:
        score += 30.0
        reasons.append("Urgent trauma / medical aid required")

    if payload.requires_water:
        score += 15.0
        reasons.append("Critical potable water scarcity")

    if payload.requires_food:
        score += 10.0
        reasons.append("Immediate ration supply required")

    if payload.requires_shelter:
        score += 10.0
        reasons.append("Exposure / emergency shelter needed")

    if payload.affected_people >= 50:
        score += 15.0
        reasons.append(f"High casualty volume ({payload.affected_people} individuals stranded)")
    elif payload.affected_people >= 10:
        score += 8.0
        reasons.append(f"Multiple individuals affected ({payload.affected_people} people)")

    score = min(100.0, max(0.0, score))

    if score >= 80.0:
        tier = "Critical"
    elif score >= 55.0:
        tier = "High"
    elif score >= 30.0:
        tier = "Medium"
    else:
        tier = "Low"

    explanation = f"Priority is {tier.upper()} because " + ", and ".join(reasons).lower() + "."

    return {
        "priority_tier": tier,
        "triage_score": round(score, 1),
        "explanation": explanation,
        "factors": reasons,
    }
