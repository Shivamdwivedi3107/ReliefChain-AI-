from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.database import get_db
from app.dependencies import get_current_active_user, require_roles
from app.models.resource import Resource, ResourceInventory
from app.models.organization import Organization
from app.models.user import User
from app.schemas.resource import (
    ResourceCreate,
    ResourceUpdate,
    ResourceOut,
    InventoryCreate,
    InventoryUpdate,
    InventoryOut,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/resources", tags=["Resources & Warehouse Inventory"])


# --- Resource Catalog ---

@router.post("", response_model=ResourceOut, status_code=status.HTTP_201_CREATED, summary="Create a new catalog resource item")
def create_resource(
    payload: ResourceCreate,
    current_user: User = Depends(require_roles(["admin", "ngo"])),
    db: Session = Depends(get_db),
):
    existing = db.query(Resource).filter(Resource.name == payload.name).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Resource item already exists")

    resource = Resource(
        name=payload.name,
        category=payload.category,
        unit=payload.unit,
        description=payload.description,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    return resource


@router.get("", response_model=List[ResourceOut], summary="List all catalog resource items")
def list_resources(
    category: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(Resource)
    if category:
        query = query.filter(Resource.category == category)
    return query.order_by(Resource.name.asc()).all()


@router.get("/{resource_id}", response_model=ResourceOut, summary="Get resource item by ID")
def get_resource_by_id(resource_id: str, db: Session = Depends(get_db)):
    res = db.query(Resource).filter(Resource.id == resource_id).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return res


# --- Organization Inventory ---

@router.post("/inventory", response_model=InventoryOut, status_code=status.HTTP_201_CREATED, summary="Add or increment warehouse inventory stock")
def add_inventory(
    payload: InventoryCreate,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    if not current_user.organization_id and current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="User must belong to an organization")

    org_id = current_user.organization_id

    # Check if resource exists
    res = db.query(Resource).filter(Resource.id == payload.resource_id).first()
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

    # Check if inventory record already exists for this org + resource
    inv = (
        db.query(ResourceInventory)
        .filter(
            ResourceInventory.organization_id == org_id,
            ResourceInventory.resource_id == payload.resource_id,
        )
        .first()
    )

    if inv:
        inv.total_quantity += payload.quantity
        inv.available_quantity += payload.quantity
        if payload.warehouse_location:
            inv.warehouse_location = payload.warehouse_location
    else:
        inv = ResourceInventory(
            organization_id=org_id,
            resource_id=payload.resource_id,
            total_quantity=payload.quantity,
            available_quantity=payload.quantity,
            reserved_quantity=0.0,
            warehouse_location=payload.warehouse_location,
        )
        db.add(inv)

    db.commit()
    db.refresh(inv)
    return inv


@router.get("/inventory/list", response_model=List[InventoryOut], summary="List warehouse inventory balances")
def list_inventory(
    organization_id: Optional[str] = Query(None),
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    query = db.query(ResourceInventory)
    if current_user.role != "admin":
        query = query.filter(ResourceInventory.organization_id == current_user.organization_id)
    elif organization_id:
        query = query.filter(ResourceInventory.organization_id == organization_id)

    return query.all()


@router.patch("/inventory/{inventory_id}", response_model=InventoryOut, summary="Update inventory quantity or location")
def update_inventory(
    inventory_id: str,
    payload: InventoryUpdate,
    current_user: User = Depends(require_roles(["ngo", "admin"])),
    db: Session = Depends(get_db),
):
    inv = db.query(ResourceInventory).filter(ResourceInventory.id == inventory_id).first()
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Inventory record not found")

    if current_user.role != "admin" and inv.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized to edit this inventory")

    if payload.total_quantity is not None:
        if payload.total_quantity < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Total quantity cannot be negative")
        inv.total_quantity = payload.total_quantity

    if payload.available_quantity is not None:
        if payload.available_quantity < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Available quantity cannot be negative")
        inv.available_quantity = payload.available_quantity

    if payload.reserved_quantity is not None:
        if payload.reserved_quantity < 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reserved quantity cannot be negative")
        inv.reserved_quantity = payload.reserved_quantity

    if payload.warehouse_location is not None:
        inv.warehouse_location = payload.warehouse_location

    db.commit()
    db.refresh(inv)
    return inv


@router.get("/alerts/low-stock", response_model=List[InventoryOut], summary="Get inventory items with low stock balances")
def get_low_stock_alerts(
    threshold: float = Query(25.0, ge=0.0, description="Available stock quantity threshold"),
    organization_id: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(ResourceInventory).filter(ResourceInventory.available_quantity <= threshold)
    if organization_id:
        query = query.filter(ResourceInventory.organization_id == organization_id)
    return query.order_by(ResourceInventory.available_quantity.asc()).all()
