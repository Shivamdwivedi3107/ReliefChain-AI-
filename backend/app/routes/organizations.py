from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.organization import Organization
from app.models.user import User
from app.models.relief_request import ReliefRequest
from app.schemas.organization import (
    OrganizationCreate,
    OrganizationUpdate,
    OrganizationOut,
)
from app.schemas.user import UserOut
from app.schemas.relief_request import ReliefRequestOut
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/organizations", tags=["Organizations & NGOs"])


@router.post("", response_model=OrganizationOut, status_code=status.HTTP_201_CREATED, summary="Create a new relief organization/NGO")
def create_organization(
    payload: OrganizationCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # Check if org name or registration number exists
    existing = db.query(Organization).filter(
        or_(
            Organization.name == payload.name,
            Organization.registration_number == payload.registration_number,
            Organization.contact_email == payload.contact_email,
        )
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An organization with this name, registration number, or email already exists.",
        )

    new_org = Organization(
        name=payload.name,
        registration_number=payload.registration_number,
        organization_type=payload.organization_type,
        contact_email=payload.contact_email,
        contact_phone=payload.contact_phone,
        address=payload.address,
        wallet_address=payload.wallet_address,
        verification_status="verified" if current_user.role == "admin" else "pending",
        is_active=True,
    )
    db.add(new_org)
    db.commit()
    db.refresh(new_org)

    # If the creator is an NGO coordinator, link them
    if current_user.role in ["ngo", "admin"] and not current_user.organization_id:
        current_user.organization_id = new_org.id
        db.commit()

    return new_org


@router.get("", response_model=PaginatedResponse[OrganizationOut], summary="List all organizations with pagination and status filter")
def list_organizations(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Organization)
    if status:
        query = query.filter(Organization.verification_status == status)
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            or_(
                Organization.name.ilike(search_pattern),
                Organization.registration_number.ilike(search_pattern),
                Organization.contact_email.ilike(search_pattern),
            )
        )

    total = query.count()
    orgs = (
        query.order_by(Organization.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PaginatedResponse(
        success=True,
        total=total,
        page=page,
        page_size=page_size,
        data=orgs,
    )


@router.get("/{org_id}", response_model=OrganizationOut, summary="Get organization profile by ID")
def get_organization_by_id(org_id: str, db: Session = Depends(get_db)):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.patch("/{org_id}", response_model=OrganizationOut, summary="Update organization profile")
def update_organization(
    org_id: str,
    payload: OrganizationUpdate,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    # Authorization check: only Admin or members of this specific organization can edit
    if current_user.role != "admin" and current_user.organization_id != org.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this organization")

    update_dict = payload.model_dump(exclude_unset=True)
    # Verification status can only be modified by admin
    if "verification_status" in update_dict and current_user.role != "admin":
        del update_dict["verification_status"]

    for k, v in update_dict.items():
        setattr(org, k, v)

    db.commit()
    db.refresh(org)
    return org


@router.patch("/{org_id}/verify", response_model=OrganizationOut, summary="Admin verify or suspend organization")
def verify_organization(
    org_id: str,
    new_status: str = Query(..., pattern="^(verified|pending|suspended)$"),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    org.verification_status = new_status
    db.commit()
    db.refresh(org)
    return org


@router.get("/{org_id}/volunteers", response_model=List[UserOut], summary="List authorized volunteers affiliated with organization")
def list_org_volunteers(
    org_id: str,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    volunteers = (
        db.query(User)
        .filter(User.organization_id == org_id, User.role == "volunteer")
        .all()
    )
    return volunteers


@router.get("/{org_id}/assigned-requests", response_model=List[ReliefRequestOut], summary="List relief requests assigned to this organization")
def list_org_assigned_requests(
    org_id: str,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    requests = (
        db.query(ReliefRequest)
        .filter(ReliefRequest.assigned_organization_id == org_id)
        .order_by(ReliefRequest.created_at.desc())
        .all()
    )
    return requests
