from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.dependencies import get_current_user, require_roles
from app.models.user import User
from app.models.incidents import DisasterEvent
from app.schemas.incident import DisasterEventOut
from app.services.disaster_intelligence_sync import disaster_sync_service
from app.services.disaster_intelligence import provider_registry

router = APIRouter(prefix="/disaster-intelligence", tags=["Disaster Intelligence Feed"])


@router.post("/sync", summary="Synchronize disaster intelligence from active feeds (Admin Only)")
async def sync_disaster_intelligence(
    provider_name: str = Query("mock_provider", description="Provider ID to synchronize"),
    auto_create_incidents: bool = Query(True, description="Automatically create operational incidents for severe alerts"),
    current_user: User = Depends(require_roles(["admin"])),
    db: Session = Depends(get_db),
):
    result = await disaster_sync_service.sync_provider(
        db=db,
        provider_name=provider_name,
        auto_create_incidents=auto_create_incidents,
        actor_id=current_user.id,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Sync failed"),
        )
    return result


@router.get("/events", response_model=List[DisasterEventOut], summary="List ingested disaster events")
def list_disaster_events(
    source: Optional[str] = Query(None, description="Filter by feed source"),
    disaster_type: Optional[str] = Query(None, description="Filter by disaster type"),
    status: Optional[str] = Query(None, description="Filter by event status (active, monitoring, resolved)"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    query = db.query(DisasterEvent)
    if source:
        query = query.filter(DisasterEvent.source == source)
    if disaster_type:
        query = query.filter(DisasterEvent.disaster_type == disaster_type.lower())
    if status:
        query = query.filter(DisasterEvent.status == status.lower())

    events = query.order_by(DisasterEvent.started_at.desc()).offset(offset).limit(limit).all()
    return events


@router.get("/providers", summary="List configured disaster intelligence feed providers")
def list_disaster_providers():
    return {
        "providers": provider_registry.list_providers(),
        "active_count": len(provider_registry.list_providers()),
    }
