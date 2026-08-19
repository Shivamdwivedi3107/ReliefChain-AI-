from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_active_user
from app.models.relief_request import ReliefRequest
from app.models.mission_history import MissionStatusHistory
from app.models.user import User
from app.schemas.mission import MissionStatusUpdate, MissionStatusHistoryOut, MissionDetailOut
from app.schemas.relief_request import ReliefRequestOut
from app.services.notification_service import notification_manager
from app.services.audit_service import audit_service
from app.services.blockchain_service import blockchain_service

router = APIRouter(prefix="/missions", tags=["Mission Operations & Lifecycle"])

# State Machine Transition Rules
ALLOWED_TRANSITIONS = {
    "pending": ["triaged", "assigned", "rejected", "cancelled"],
    "under_review": ["triaged", "assigned", "rejected", "cancelled"],
    "triaged": ["assigned", "dispatched", "rejected", "cancelled"],
    "assigned": ["dispatched", "in_progress", "cancelled"],
    "dispatched": ["in_progress", "delivered", "cancelled"],
    "in_progress": ["delivered", "completed", "cancelled"],
    "delivered": ["completed"],
    "completed": [],
    "rejected": [],
    "cancelled": [],
}


@router.get("", summary="List missions with role-scoped access control")
def list_missions(
    status_filter: Optional[str] = Query(None, alias="status"),
    priority_filter: Optional[str] = Query(None, alias="priority"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(ReliefRequest)

    # Role-based scoping
    if current_user.role in ["citizen", "beneficiary"]:
        query = query.filter(ReliefRequest.citizen_id == current_user.id)
    elif current_user.role == "volunteer":
        query = query.filter(ReliefRequest.assigned_volunteer_id == current_user.id)
    elif current_user.role in ["ngo", "relief_organization"]:
        if current_user.organization_id:
            query = query.filter(ReliefRequest.assigned_organization_id == current_user.organization_id)

    if status_filter:
        query = query.filter(ReliefRequest.status == status_filter.lower())
    if priority_filter:
        query = query.filter(ReliefRequest.priority == priority_filter.lower())

    total = query.count()
    missions = (
        query.order_by(ReliefRequest.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "data": [ReliefRequestOut.model_validate(m) for m in missions],
    }


@router.get("/{mission_id}", response_model=MissionDetailOut, summary="Get mission details by ID")
def get_mission_by_id(
    mission_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    mission = db.query(ReliefRequest).filter(ReliefRequest.id == mission_id).first()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESOURCE_NOT_FOUND", "message": f"Mission {mission_id} not found"},
        )

    # Check permission
    if current_user.role in ["citizen", "beneficiary"] and mission.citizen_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to this mission")
    if current_user.role == "volunteer" and mission.assigned_volunteer_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied to unassigned mission")

    return mission


@router.patch("/{mission_id}/status", response_model=ReliefRequestOut, summary="Update mission status with transition validation")
def update_mission_status(
    mission_id: str,
    payload: MissionStatusUpdate,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    mission = db.query(ReliefRequest).filter(ReliefRequest.id == mission_id).first()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESOURCE_NOT_FOUND", "message": f"Mission {mission_id} not found"},
        )

    prev_status = mission.status
    target_status = payload.new_status.lower()

    # 1. Role Permission Validation
    if current_user.role in ["citizen", "beneficiary"]:
        if mission.citizen_id != current_user.id or target_status != "cancelled":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Citizens can only cancel their own pending requests")

    elif current_user.role == "volunteer":
        if mission.assigned_volunteer_id != current_user.id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Volunteer not assigned to this mission")
        if target_status not in ["in_progress", "delivered"]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Volunteers cannot transition mission to '{target_status}'")

    elif current_user.role in ["ngo", "relief_organization"]:
        if current_user.organization_id and mission.assigned_organization_id != current_user.organization_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Mission not assigned to your organization")

    # 2. State Machine Validation
    allowed = ALLOWED_TRANSITIONS.get(prev_status, [])
    if target_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "INVALID_STATUS_TRANSITION",
                "message": f"Cannot transition mission from '{prev_status}' to '{target_status}'. Allowed transitions: {allowed}",
            },
        )

    # 3. Update Status
    mission.status = target_status

    # 4. Save Status History
    history = MissionStatusHistory(
        relief_request_id=mission.id,
        previous_status=prev_status,
        new_status=target_status,
        changed_by_user_id=current_user.id,
        optional_note=payload.note,
    )
    db.add(history)

    # 5. Audit Log
    client_ip = request.client.host if request.client else None
    audit_service.log_action(
        db=db,
        action="mission_status_change",
        entity_type="relief_request",
        entity_id=mission.id,
        user_id=current_user.id,
        details={"previous_status": prev_status, "new_status": target_status, "note": payload.note},
        ip_address=client_ip,
    )

    # 6. Notifications
    # Notify Citizen
    if mission.citizen_id:
        notification_manager.create_notification(
            db=db,
            user_id=mission.citizen_id,
            title="Mission Status Updated",
            message=f"Your relief request for {mission.location_name} is now: {target_status.upper()}",
            notification_type="mission_update",
            severity="info" if target_status != "completed" else "success",
            reference_id=mission.id,
            reference_type="relief_request",
        )

    # Notify Volunteer if assigned
    if mission.assigned_volunteer_id and mission.assigned_volunteer_id != current_user.id:
        notification_manager.create_notification(
            db=db,
            user_id=mission.assigned_volunteer_id,
            title="Mission Assignment Update",
            message=f"Mission at {mission.location_name} status updated to {target_status.upper()}",
            notification_type="mission_update",
            severity="info",
            reference_id=mission.id,
            reference_type="relief_request",
        )

    # 7. Transparency Ledger (for delivered or completed milestones)
    if target_status in ["delivered", "completed", "cancelled"]:
        blockchain_service.log_event(
            db=db,
            event_type=f"MISSION_{target_status.upper()}",
            payload={
                "relief_request_id": mission.id,
                "previous_status": prev_status,
                "new_status": target_status,
                "changed_by": current_user.id,
            },
        )

    db.commit()
    db.refresh(mission)
    return mission


@router.get("/{mission_id}/history", response_model=List[MissionStatusHistoryOut], summary="Get mission status change history")
def get_mission_status_history(
    mission_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    mission = db.query(ReliefRequest).filter(ReliefRequest.id == mission_id).first()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESOURCE_NOT_FOUND", "message": f"Mission {mission_id} not found"},
        )

    history = (
        db.query(MissionStatusHistory)
        .filter(MissionStatusHistory.relief_request_id == mission_id)
        .order_by(MissionStatusHistory.created_at.asc())
        .all()
    )

    return history


@router.get("/{mission_id}/recommended-volunteers", summary="Get intelligent ranked volunteer recommendations for a mission")
def get_recommended_volunteers_for_mission(
    mission_id: str,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    from app.services.recommendation_service import recommendation_engine
    
    # Verify mission existence
    mission = db.query(ReliefRequest).filter(ReliefRequest.id == mission_id).first()
    if not mission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "RESOURCE_NOT_FOUND", "message": f"Mission with ID '{mission_id}' was not found."},
        )

    recommendations = recommendation_engine.get_recommendations_for_mission(
        db=db,
        mission_id=mission_id,
        max_results=limit,
    )
    return {
        "success": True,
        "mission_id": mission_id,
        "disaster_type": mission.disaster_type,
        "location_name": mission.location_name,
        "priority": mission.priority,
        "recommendations": recommendations.get("recommendations", []),
        "disclaimer": "Recommendations are generated by the DSS engine based on proximity, skills, workload, and availability. Assignment requires NGO or Admin authorization.",
    }
