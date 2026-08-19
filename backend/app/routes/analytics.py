from typing import Dict, Any, List, Optional
from datetime import datetime
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
from app.models.resource import Resource, ResourceInventory

router = APIRouter(prefix="/analytics", tags=["Analytics & Operational Reports"])


@router.get("/overview", summary="High-level platform KPI analytics overview")
def get_analytics_overview(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_reqs = db.query(func.count(ReliefRequest.id)).scalar() or 0
    pending_reqs = db.query(func.count(ReliefRequest.id)).filter(ReliefRequest.status == "pending").scalar() or 0
    critical_reqs = db.query(func.count(ReliefRequest.id)).filter(ReliefRequest.priority == "critical").scalar() or 0
    
    active_missions = db.query(func.count(ReliefRequest.id)).filter(
        ReliefRequest.status.in_(["assigned", "dispatched", "in_progress", "triaged"])
    ).scalar() or 0
    completed_missions = db.query(func.count(ReliefRequest.id)).filter(ReliefRequest.status == "completed").scalar() or 0

    total_dists = db.query(func.count(Distribution.id)).scalar() or 0
    completed_dists = db.query(func.count(Distribution.id)).filter(Distribution.status.in_(["verified", "completed"])).scalar() or 0

    total_donations_count = db.query(func.count(Donation.id)).scalar() or 0
    total_donations_usd = db.query(func.sum(Donation.amount)).filter(Donation.donation_type == "monetary").scalar() or 0.0

    low_stock_count = db.query(func.count(ResourceInventory.id)).filter(ResourceInventory.available_quantity < 30.0).scalar() or 0
    total_bc_records = db.query(func.count(BlockchainTransaction.id)).scalar() or 0

    return {
        "total_requests": total_reqs,
        "pending_requests": pending_reqs,
        "critical_requests": critical_reqs,
        "active_missions": active_missions,
        "completed_missions": completed_missions,
        "total_distributions": total_dists,
        "completed_distributions": completed_dists,
        "total_donations": total_donations_count,
        "total_donations_usd": round(float(total_donations_usd), 2),
        "low_stock_items": low_stock_count,
        "blockchain_audit_proofs": total_bc_records,
        "kpi": {
            "total_requests": total_reqs,
            "completed_requests": completed_missions,
            "pending_requests": pending_reqs,
            "total_donations_usd": round(float(total_donations_usd), 2),
            "total_distributions": total_dists,
            "verified_distributions": completed_dists,
            "delivery_verification_rate_pct": round((completed_dists / total_dists * 100), 1) if total_dists > 0 else 100.0,
            "blockchain_audit_proofs": total_bc_records,
        },
    }


@router.get("/priority-distribution", summary="Requests aggregated by priority classification")
@router.get("/priority-breakdown", summary="Alias for priority distribution")
def get_priority_distribution(db: Session = Depends(get_db)) -> Dict[str, int]:
    rows = (
        db.query(ReliefRequest.priority, func.count(ReliefRequest.id).label("count"))
        .group_by(ReliefRequest.priority)
        .all()
    )
    result = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for p, c in rows:
        key = (p or "medium").lower()
        result[key] = c
    return result


@router.get("/disaster-types", summary="Requests aggregated by disaster type")
@router.get("/disasters-breakdown", summary="Alias for disaster breakdown")
def get_disaster_types(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    rows = (
        db.query(ReliefRequest.disaster_type, func.count(ReliefRequest.id).label("count"))
        .group_by(ReliefRequest.disaster_type)
        .order_by(desc("count"))
        .all()
    )
    return [{"disaster_type": r[0], "count": r[1]} for r in rows]


@router.get("/mission-performance", summary="Mission execution and turnaround performance metrics")
def get_mission_performance(db: Session = Depends(get_db)) -> Dict[str, Any]:
    completed = db.query(ReliefRequest).filter(ReliefRequest.status == "completed").all()
    active = db.query(func.count(ReliefRequest.id)).filter(
        ReliefRequest.status.in_(["assigned", "dispatched", "in_progress", "triaged"])
    ).scalar() or 0
    cancelled = db.query(func.count(ReliefRequest.id)).filter(
        ReliefRequest.status.in_(["cancelled", "rejected"])
    ).scalar() or 0

    # Calculate average completion time if timestamps available
    completion_times_hours = []
    for r in completed:
        if r.created_at and r.updated_at and r.updated_at > r.created_at:
            delta = (r.updated_at - r.created_at).total_seconds() / 3600.0
            completion_times_hours.append(delta)

    avg_time = round(sum(completion_times_hours) / len(completion_times_hours), 2) if completion_times_hours else None

    return {
        "completed_missions": len(completed),
        "active_missions": active,
        "cancelled_missions": cancelled,
        "average_completion_time_hours": avg_time,
        "has_timing_metrics": bool(completion_times_hours),
    }


@router.get("/inventory-summary", summary="Warehouse depot inventory availability summary")
def get_inventory_summary(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_items = db.query(func.count(Resource.id)).scalar() or 0
    available_stock = db.query(func.sum(ResourceInventory.available_quantity)).scalar() or 0.0
    reserved_stock = db.query(func.sum(ResourceInventory.reserved_quantity)).scalar() or 0.0
    total_stock = db.query(func.sum(ResourceInventory.total_quantity)).scalar() or 0.0
    low_stock_count = db.query(func.count(ResourceInventory.id)).filter(ResourceInventory.available_quantity < 30.0).scalar() or 0

    return {
        "total_catalog_items": total_items,
        "available_stock": round(float(available_stock), 2),
        "reserved_stock": round(float(reserved_stock), 2),
        "total_stock": round(float(total_stock), 2),
        "low_stock_count": low_stock_count,
    }


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


@router.get("/ai-intelligence", summary="Aggregated AI DSS, Risk Forecasting, and Model Governance analytics")
def get_ai_intelligence_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    from app.models.ai_models import DisasterRiskPredictionRecord, ResourceForecastRecord, DisasterSimulationRecord
    from app.models.prediction import PredictionHistory
    from app.services.model_registry import model_registry

    total_risk_records = db.query(func.count(DisasterRiskPredictionRecord.id)).scalar() or 0
    avg_risk_score = db.query(func.avg(DisasterRiskPredictionRecord.risk_score)).scalar() or 62.5
    high_risk_count = db.query(func.count(DisasterRiskPredictionRecord.id)).filter(
        DisasterRiskPredictionRecord.risk_level.in_(["HIGH", "CRITICAL"])
    ).scalar() or 0

    total_forecasts = db.query(func.count(ResourceForecastRecord.id)).scalar() or 0
    total_simulations = db.query(func.count(DisasterSimulationRecord.id)).scalar() or 0
    total_triage_preds = db.query(func.count(PredictionHistory.id)).scalar() or 0

    models = model_registry.list_models()
    active_models_count = sum(1 for m in models if m.get("is_active"))

    return {
        "success": True,
        "total_risk_assessments": total_risk_records,
        "average_risk_score": round(float(avg_risk_score), 1),
        "high_hazard_alerts": high_risk_count,
        "total_resource_forecasts": total_forecasts,
        "total_disaster_simulations": total_simulations,
        "total_emergency_triage_predictions": total_triage_preds,
        "active_ai_models_count": active_models_count,
        "models_catalog_summary": models,
        "decision_support_notice": "Analytics are aggregated across live AI decision-support interactions.",
    }

