from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.core.security import get_password_hash
from app.models.user import User
from app.models.relief_request import ReliefRequest
from app.schemas.user import UserOut, UserUpdate
from app.schemas.relief_request import ReliefRequestOut
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/users", tags=["Users & Profiles"])


@router.get("/me", response_model=UserOut, summary="Get profile of current user")
def get_my_profile(current_user: User = Depends(get_current_active_user)):
    return current_user


@router.patch("/me", response_model=UserOut, summary="Update profile of current user")
def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    if payload.full_name is not None:
        current_user.full_name = payload.full_name
    if payload.phone_number is not None:
        current_user.phone_number = payload.phone_number
    if payload.password is not None:
        current_user.hashed_password = get_password_hash(payload.password)

    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/me/requests", response_model=List[ReliefRequestOut], summary="Get distress requests filed by current user")
def get_my_relief_requests(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    requests = (
        db.query(ReliefRequest)
        .filter(ReliefRequest.citizen_id == current_user.id)
        .order_by(ReliefRequest.created_at.desc())
        .all()
    )
    return requests


@router.get("", response_model=PaginatedResponse[UserOut], summary="Admin list all users with pagination")
def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    role: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    query = db.query(User)

    if role:
        query = query.filter(User.role == role)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                User.full_name.ilike(search_pattern),
                User.email.ilike(search_pattern),
            )
        )

    total = query.count()
    users = (
        query.order_by(User.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        data=users,
    )


@router.get("/{user_id}", response_model=UserOut, summary="Get user details by ID")
def get_user_by_id(
    user_id: str,
    current_user: User = Depends(require_roles(["admin", "ngo"])),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return user


@router.patch("/{user_id}/role", response_model=UserOut, summary="Admin update user role")
def update_user_role(
    user_id: str,
    new_role: str = Query(..., pattern="^(citizen|ngo|volunteer|admin)$"),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.role = new_role
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/status", response_model=UserOut, summary="Admin toggle user active status")
def toggle_user_status(
    user_id: str,
    is_active: bool = Query(...),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.is_active = is_active
    db.commit()
    db.refresh(user)
    return user
