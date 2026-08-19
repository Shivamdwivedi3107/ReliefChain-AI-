from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.incidents import Incident, SituationReport
from app.schemas.incident import SituationReportCreate, SituationReportOut
from app.services.incident_service import incident_service

router = APIRouter(prefix="/situation-reports", tags=["Situation Reports (SITREP)"])


@router.post("", response_model=SituationReportOut, status_code=status.HTTP_201_CREATED, summary="Submit a new structured Situation Report")
def create_situation_report(
    payload: SituationReportCreate,
    current_user: User = Depends(require_roles(["volunteer", "ngo", "admin"])),
    db: Session = Depends(get_db),
):
    incident = db.query(Incident).filter(Incident.id == payload.incident_id).first()
    if not incident:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Referenced incident not found")

    sitrep = SituationReport(
        incident_id=payload.incident_id,
        author_id=current_user.id,
        report_type=payload.report_type,
        summary=payload.summary,
        people_affected=payload.people_affected,
        people_displaced=payload.people_displaced,
        casualties_reported=payload.casualties_reported,
        infrastructure_damage_level=payload.infrastructure_damage_level,
        medical_need_level=payload.medical_need_level,
        food_need_level=payload.food_need_level,
        water_need_level=payload.water_need_level,
        shelter_need_level=payload.shelter_need_level,
        communication_status=payload.communication_status,
        latitude=payload.latitude or incident.latitude,
        longitude=payload.longitude or incident.longitude,
    )
    db.add(sitrep)
    db.flush()

    # Append timeline entry on the parent incident
    incident_service.add_timeline_entry(
        db=db,
        incident_id=incident.id,
        event_type="SITREP_SUBMITTED",
        message=f"[{payload.report_type.upper()} SITREP] by {current_user.full_name}: {payload.summary[:100]}...",
        actor_id=current_user.id,
        metadata_json={
            "sitrep_id": sitrep.id,
            "report_type": payload.report_type,
            "casualties": payload.casualties_reported,
            "displaced": payload.people_displaced,
        },
    )
    db.commit()
    db.refresh(sitrep)
    return sitrep


@router.get("", response_model=List[SituationReportOut], summary="List situation reports across incidents")
def list_situation_reports(
    incident_id: Optional[str] = Query(None, description="Filter by incident ID"),
    report_type: Optional[str] = Query(None, description="Filter by report type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(SituationReport)
    if incident_id:
        query = query.filter(SituationReport.incident_id == incident_id)
    if report_type:
        query = query.filter(SituationReport.report_type == report_type)

    reports = query.order_by(SituationReport.created_at.desc()).offset(offset).limit(limit).all()
    return reports


@router.get("/{report_id}", response_model=SituationReportOut, summary="Retrieve situation report by ID")
def get_situation_report(
    report_id: str,
    db: Session = Depends(get_db),
):
    sitrep = db.query(SituationReport).filter(SituationReport.id == report_id).first()
    if not sitrep:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Situation report not found")
    return sitrep


@router.get("/incident/{incident_id}", response_model=List[SituationReportOut], summary="Get all situation reports for an incident")
def get_incident_situation_reports(
    incident_id: str,
    db: Session = Depends(get_db),
):
    reports = (
        db.query(SituationReport)
        .filter(SituationReport.incident_id == incident_id)
        .order_by(SituationReport.created_at.desc())
        .all()
    )
    return reports
