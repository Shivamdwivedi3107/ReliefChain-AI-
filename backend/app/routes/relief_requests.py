from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.relief_request import ReliefRequest
from app.models.user import User
from app.models.organization import Organization
from app.models.prediction import PredictionHistory
from app.models.notification import Notification
from app.schemas.relief_request import (
    ReliefRequestCreate,
    ReliefRequestUpdate,
    ReliefRequestAssign,
    ReliefRequestOut,
)
from app.schemas.common import PaginatedResponse
from app.services.ai_service import predict_emergency_priority

router = APIRouter(prefix="/relief-requests", tags=["Relief Requests"])


@router.post("", response_model=ReliefRequestOut, status_code=status.HTTP_201_CREATED, summary="Create an emergency relief request with AI triage scoring")
def create_relief_request(
    payload: ReliefRequestCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Detect resource requirements for AI scoring
    req_json = payload.required_resources or []
    req_str = str(req_json).lower() + " " + (payload.urgency_description or "").lower()

    medical_needed = 1 if ("med" in req_str or "injur" in req_str or "trauma" in req_str or "health" in req_str) else 0
    water_needed = 1 if ("water" in req_str or "drink" in req_str or "dehydrat" in req_str) else 0
    food_needed = 1 if ("food" in req_str or "ration" in req_str or "meal" in req_str or "grain" in req_str) else 0
    vulnerable_needed = 1 if ("child" in req_str or "infant" in req_str or "elderly" in req_str or "pregnant" in req_str) else 0

    # Run AI Decision Support Prioritization
    predicted_priority, confidence, factors = predict_emergency_priority(
        disaster_type=payload.disaster_type,
        affected_people=payload.affected_people,
        location_risk_score=5.0,
        food_needed=food_needed,
        water_needed=water_needed,
        medical_needed=medical_needed,
        vulnerable_population=vulnerable_needed,
    )

    new_request = ReliefRequest(
        citizen_id=current_user.id,
        disaster_id=payload.disaster_id,
        disaster_type=payload.disaster_type,
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        affected_people=payload.affected_people,
        required_resources=payload.required_resources,
        urgency_description=payload.urgency_description,
        image_reference=payload.image_reference,
        priority=predicted_priority,
        status="pending",
        ai_predicted_priority=predicted_priority,
        ai_confidence=confidence,
        ai_factors=factors,
    )
    db.add(new_request)
    db.commit()
    db.refresh(new_request)

    # Save Prediction History record
    pred_history = PredictionHistory(
        request_id=new_request.id,
        disaster_type=payload.disaster_type,
        affected_people=payload.affected_people,
        location_risk_score=5.0,
        medical_needed=medical_needed,
        food_needed=food_needed,
        water_needed=water_needed,
        vulnerable_population=vulnerable_needed,
        predicted_priority=predicted_priority,
        confidence_score=confidence,
        contributing_factors=factors,
    )
    db.add(pred_history)

    # Send Notification to Citizen
    notif = Notification(
        user_id=current_user.id,
        title="Relief Request Submitted",
        message=f"Your relief request for '{payload.location_name}' has been registered with priority '{predicted_priority.upper()}'.",
        notification_type="status_update",
        reference_id=new_request.id,
        reference_type="relief_request",
    )
    db.add(notif)
    db.commit()

    return new_request


@router.get("", response_model=PaginatedResponse[ReliefRequestOut], summary="List relief requests with filters and pagination")
def list_relief_requests(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    disaster_type: Optional[str] = Query(None),
    disaster_id: Optional[str] = Query(None),
    organization_id: Optional[str] = Query(None),
    volunteer_id: Optional[str] = Query(None),
    location: Optional[str] = Query(None, description="Search by location substring"),
    sort_by: Optional[str] = Query("created_at", description="Sort field: created_at, priority, urgency, affected_people"),
    db: Session = Depends(get_db),
):
    query = db.query(ReliefRequest)
    if status:
        query = query.filter(ReliefRequest.status == status)
    if priority:
        query = query.filter(ReliefRequest.priority == priority)
    if disaster_type:
        query = query.filter(ReliefRequest.disaster_type == disaster_type)
    if disaster_id:
        query = query.filter(ReliefRequest.disaster_id == disaster_id)
    if organization_id:
        query = query.filter(ReliefRequest.assigned_organization_id == organization_id)
    if volunteer_id:
        query = query.filter(ReliefRequest.assigned_volunteer_id == volunteer_id)
    if location:
        query = query.filter(ReliefRequest.location_name.ilike(f"%{location}%"))

    total = query.count()

    if sort_by in ["priority", "urgency"]:
        # Custom priority hierarchy order: critical > high > medium > low
        from sqlalchemy import case
        priority_order = case(
            (ReliefRequest.priority == "critical", 1),
            (ReliefRequest.priority == "high", 2),
            (ReliefRequest.priority == "medium", 3),
            (ReliefRequest.priority == "low", 4),
            else_=5,
        )
        query = query.order_by(priority_order, ReliefRequest.created_at.desc())
    elif sort_by == "affected_people":
        query = query.order_by(ReliefRequest.affected_people.desc(), ReliefRequest.created_at.desc())
    else:
        query = query.order_by(ReliefRequest.created_at.desc())

    items = (
        query.offset((page - 1) * page_size)
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


@router.get("/{request_id}", response_model=ReliefRequestOut, summary="Get relief request details by ID")
def get_relief_request_by_id(request_id: str, db: Session = Depends(get_db)):
    req = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relief request not found")
    return req


@router.patch("/{request_id}", response_model=ReliefRequestOut, summary="Update relief request status or attributes")
def update_relief_request(
    request_id: str,
    payload: ReliefRequestUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    req = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relief request not found")

    # Only creator, assigned volunteer, assigned NGO, or Admin can update
    is_owner = req.citizen_id == current_user.id
    is_admin = current_user.role == "admin"
    is_org_member = current_user.organization_id and current_user.organization_id == req.assigned_organization_id
    is_volunteer = req.assigned_volunteer_id == current_user.id

    if not (is_owner or is_admin or is_org_member or is_volunteer):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to modify this request")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(req, k, v)

    db.commit()
    db.refresh(req)

    # Notify Citizen of status change
    if "status" in update_dict:
        notif = Notification(
            user_id=req.citizen_id,
            title="Request Status Updated",
            message=f"Your relief request for '{req.location_name}' is now '{req.status.upper()}'.",
            notification_type="status_update",
            reference_id=req.id,
            reference_type="relief_request",
        )
        db.add(notif)
        db.commit()

    return req


@router.post("/{request_id}/assign", response_model=ReliefRequestOut, summary="Assign NGO and field volunteer to relief request")
def assign_relief_request(
    request_id: str,
    payload: ReliefRequestAssign,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    req = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relief request not found")

    if payload.assigned_organization_id:
        org = db.query(Organization).filter(Organization.id == payload.assigned_organization_id).first()
        if not org:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
        req.assigned_organization_id = payload.assigned_organization_id

    if payload.assigned_volunteer_id:
        volunteer = db.query(User).filter(User.id == payload.assigned_volunteer_id, User.role == "volunteer").first()
        if not volunteer:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Volunteer not found")
        req.assigned_volunteer_id = payload.assigned_volunteer_id

        # Notify Volunteer
        notif_vol = Notification(
            user_id=volunteer.id,
            title="New Mission Assignment",
            message=f"You have been assigned to relief request at '{req.location_name}'.",
            notification_type="assignment",
            reference_id=req.id,
            reference_type="relief_request",
        )
        db.add(notif_vol)

    req.status = "assigned"
    db.commit()
    db.refresh(req)

    # Notify Citizen
    notif_cit = Notification(
        user_id=req.citizen_id,
        title="Request Assigned to Field Responders",
        message=f"Your relief request has been assigned to response team and is being processed.",
        notification_type="status_update",
        reference_id=req.id,
        reference_type="relief_request",
    )
    db.add(notif_cit)
    db.commit()

    return req


@router.delete("/{request_id}", status_code=status.HTTP_200_OK, summary="Cancel or delete a relief request")
def delete_relief_request(
    request_id: str,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    req = db.query(ReliefRequest).filter(ReliefRequest.id == request_id).first()
    if not req:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Relief request not found")

    is_owner = req.citizen_id == current_user.id
    is_admin = current_user.role == "admin"
    if not (is_owner or is_admin):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to delete this request")

    if req.status in ["completed", "in_progress"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete request in '{req.status}' state. You may mark it rejected or cancel instead."
        )

    db.delete(req)
    db.commit()
    return {"success": True, "message": "Relief request deleted successfully", "id": request_id}
