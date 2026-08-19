from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.disaster import Disaster
from app.models.user import User
from app.schemas.disaster import DisasterCreate, DisasterUpdate, DisasterOut
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/disasters", tags=["Disasters"])


@router.post("", response_model=DisasterOut, status_code=status.HTTP_201_CREATED, summary="Create a new disaster incident")
def create_disaster(
    payload: DisasterCreate,
    current_user: User = Depends(require_roles(["admin", "ngo"])),
    db: Session = Depends(get_db),
):
    disaster = Disaster(
        title=payload.title,
        disaster_type=payload.disaster_type,
        severity=payload.severity,
        location_name=payload.location_name,
        latitude=payload.latitude,
        longitude=payload.longitude,
        radius_km=payload.radius_km,
        description=payload.description,
        started_at=payload.started_at,
        status="active",
    )
    db.add(disaster)
    db.commit()
    db.refresh(disaster)
    return disaster


@router.get("", response_model=PaginatedResponse[DisasterOut], summary="List disasters with status and search filters")
def list_disasters(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Disaster)
    if status:
        query = query.filter(Disaster.status == status)
    if severity:
        query = query.filter(Disaster.severity == severity)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Disaster.title.ilike(search_pattern),
                Disaster.location_name.ilike(search_pattern),
                Disaster.disaster_type.ilike(search_pattern),
            )
        )

    total = query.count()
    items = (
        query.order_by(Disaster.created_at.desc())
        .offset((page - 1) * page_size)
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


@router.get("/{disaster_id}", response_model=DisasterOut, summary="Get disaster details by ID")
def get_disaster_by_id(disaster_id: str, db: Session = Depends(get_db)):
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disaster not found")
    return disaster


@router.patch("/{disaster_id}", response_model=DisasterOut, summary="Update disaster incident status or details")
def update_disaster(
    disaster_id: str,
    payload: DisasterUpdate,
    current_user: User = Depends(require_roles(["admin", "ngo"])),
    db: Session = Depends(get_db),
):
    disaster = db.query(Disaster).filter(Disaster.id == disaster_id).first()
    if not disaster:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Disaster not found")

    update_dict = payload.model_dump(exclude_unset=True)
    for k, v in update_dict.items():
        setattr(disaster, k, v)

    db.commit()
    db.refresh(disaster)
    return disaster
