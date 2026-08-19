from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_roles, get_current_user_optional
from app.models.user import User
from app.models.incidents import Incident, IncidentTimeline
from app.schemas.incident import (
    IncidentCreate,
    IncidentUpdate,
    IncidentOut,
    IncidentTimelineOut,
    IncidentTransitionAction,
)
from app.services.incident_service import incident_service
from app.services.escalation_service import escalation_service

router = APIRouter(prefix="/incidents", tags=["Incident Management"])


@router.post("", response_model=IncidentOut, status_code=status.HTTP_201_CREATED, summary="Create a new disaster incident")
def create_incident(
    payload: IncidentCreate,
    current_user: User = Depends(require_roles(["ngo", "admin", "volunteer"])),
    db: Session = Depends(get_db),
):
    incident = incident_service.create_incident(
        db=db,
        title=payload.title,
        disaster_type=payload.disaster_type,
        severity=payload.severity,
        latitude=payload.latitude,
        longitude=payload.longitude,
        affected_radius_km=payload.affected_radius_km,
        event_id=payload.event_id,
        organization_id=payload.organization_id or current_user.organization_id,
        description=payload.description,
        metadata_json=payload.metadata_json,
        actor_id=current_user.id,
    )
    return incident


@router.get("", response_model=List[IncidentOut], summary="List incidents with filtering and pagination")
def list_incidents(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status (DETECTED, VERIFIED, ACTIVE, etc.)"),
    disaster_type: Optional[str] = Query(None, description="Filter by disaster type"),
    escalation_level: Optional[str] = Query(None, description="Filter by escalation tier"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db),
):
    query = db.query(Incident)

    # If citizen or unauthenticated, hide CANCELLED and show public-visible states
    if not current_user or current_user.role == "citizen":
        query = query.filter(Incident.status.notin_(["CANCELLED"]))

    if status_filter:
        query = query.filter(Incident.status == status_filter.upper())
    if disaster_type:
        query = query.filter(Incident.disaster_type == disaster_type.lower())
    if escalation_level:
        query = query.filter(Incident.escalation_level == escalation_level.upper())

    incidents = query.order_by(Incident.created_at.desc()).offset(offset).limit(limit).all()
    return incidents


@router.get("/{incident_id}", response_model=IncidentOut, summary="Retrieve incident details by ID")
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return incident


@router.patch("/{incident_id}", response_model=IncidentOut, summary="Update incident parameters")
def update_incident(
    incident_id: str,
    payload: IncidentUpdate,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    update_dict = payload.model_dump(exclude_unset=True)
    # If direct status update requested via PATCH, validate transition
    if "status" in update_dict and update_dict["status"]:
        incident_service.transition_status(
            db=db,
            incident=incident,
            target_status=update_dict["status"],
            actor=current_user,
            note="Updated via incident PATCH API",
        )
        del update_dict["status"]

    for k, v in update_dict.items():
        setattr(incident, k, v)

    db.commit()
    db.refresh(incident)
    return incident


@router.post("/{incident_id}/verify", response_model=IncidentOut, summary="Transition incident status to VERIFIED")
def verify_incident(
    incident_id: str,
    payload: IncidentTransitionAction = IncidentTransitionAction(),
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    return incident_service.transition_status(
        db=db,
        incident=incident,
        target_status="VERIFIED",
        actor=current_user,
        note=payload.note,
    )


@router.post("/{incident_id}/activate", response_model=IncidentOut, summary="Transition incident status to ACTIVE")
def activate_incident(
    incident_id: str,
    payload: IncidentTransitionAction = IncidentTransitionAction(),
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    return incident_service.transition_status(
        db=db,
        incident=incident,
        target_status="ACTIVE",
        actor=current_user,
        note=payload.note,
    )


@router.post("/{incident_id}/resolve", response_model=IncidentOut, summary="Transition incident status to RESOLVED")
def resolve_incident(
    incident_id: str,
    payload: IncidentTransitionAction = IncidentTransitionAction(),
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    return incident_service.transition_status(
        db=db,
        incident=incident,
        target_status="RESOLVED",
        actor=current_user,
        note=payload.note,
    )


@router.get("/{incident_id}/timeline", response_model=List[IncidentTimelineOut], summary="Retrieve chronological append-only incident timeline")
def get_incident_timeline(
    incident_id: str,
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    timelines = (
        db.query(IncidentTimeline)
        .filter(IncidentTimeline.incident_id == incident_id)
        .order_by(IncidentTimeline.created_at.asc())
        .all()
    )
    return timelines


@router.post("/{incident_id}/evaluate-escalation", summary="Run multi-factor disaster escalation calculation")
def evaluate_incident_escalation(
    incident_id: str,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")

    result = escalation_service.calculate_escalation(
        db=db,
        incident=incident,
        auto_update_incident=True,
    )
    return {
        "success": True,
        "escalation_analysis": result,
    }
