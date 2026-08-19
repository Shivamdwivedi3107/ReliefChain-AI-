from collections import Counter
from typing import Dict, Any, List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.incidents import Incident, IncidentTimeline, SituationReport
from app.models.relief_request import ReliefRequest
from app.models.user import User

router = APIRouter(prefix="/command-center", tags=["Incident Command Center"])


@router.get("/summary", summary="Retrieve aggregated Incident Command Center operational overview")
def get_command_center_summary(db: Session = Depends(get_db)):
    # Incidents metrics
    all_incidents = db.query(Incident).filter(Incident.status.notin_(["CANCELLED"])).all()
    active_incidents = [i for i in all_incidents if i.status not in ("RESOLVED", "CANCELLED")]

    # By Severity
    sev_dist = {"critical": 0, "high": 0, "moderate": 0, "low": 0}
    for i in active_incidents:
        if i.severity >= 8.0:
            sev_dist["critical"] += 1
        elif i.severity >= 6.0:
            sev_dist["high"] += 1
        elif i.severity >= 4.0:
            sev_dist["moderate"] += 1
        else:
            sev_dist["low"] += 1

    # By Disaster Type
    type_counts = Counter(i.disaster_type for i in active_incidents)

    # Escalation Distribution
    escalation_dist = Counter(i.escalation_level for i in active_incidents)

    # Unresolved SOS Requests
    unresolved_sos = (
        db.query(ReliefRequest)
        .filter(ReliefRequest.status.in_(["pending", "triaged", "assigned", "dispatched"]))
        .count()
    )

    # Active / Available Volunteers
    available_volunteers = (
        db.query(User)
        .filter(User.role == "volunteer", User.is_active == True)
        .count()
    )

    # Recent SITREPs
    recent_sitreps_raw = (
        db.query(SituationReport)
        .order_by(SituationReport.created_at.desc())
        .limit(5)
        .all()
    )
    recent_sitreps = [
        {
            "id": s.id,
            "incident_id": s.incident_id,
            "report_type": s.report_type,
            "summary": s.summary,
            "casualties": s.casualties_reported,
            "displaced": s.people_displaced,
            "created_at": s.created_at.isoformat() if s.created_at else None,
        }
        for s in recent_sitreps_raw
    ]

    # Recent Timeline entries
    recent_timelines_raw = (
        db.query(IncidentTimeline)
        .order_by(IncidentTimeline.created_at.desc())
        .limit(8)
        .all()
    )
    recent_timelines = [
        {
            "id": t.id,
            "incident_id": t.incident_id,
            "event_type": t.event_type,
            "message": t.message,
            "created_at": t.created_at.isoformat() if t.created_at else None,
        }
        for t in recent_timelines_raw
    ]

    return {
        "active_incidents_count": len(active_incidents),
        "total_incidents_tracked": len(all_incidents),
        "incidents_by_severity": sev_dist,
        "incidents_by_type": dict(type_counts),
        "critical_incidents_count": sev_dist["critical"],
        "unresolved_sos_requests_count": unresolved_sos,
        "volunteer_availability_count": available_volunteers,
        "current_escalation_distribution": dict(escalation_dist),
        "recent_situation_reports": recent_sitreps,
        "recent_timeline_activity": recent_timelines,
        "system_readiness": "OPERATIONAL",
    }
