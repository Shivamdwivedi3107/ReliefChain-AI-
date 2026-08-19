from typing import Dict, Any
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.shortage_radar_service import shortage_radar_service

router = APIRouter(prefix="/resources", tags=["Resource Shortage Radar"])


@router.get("/shortage-radar", summary="Get real-time resource shortage radar matrix")
def get_shortage_radar(
    horizon_days: int = Query(3, ge=1, le=14, description="Forecast horizon in days"),
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Returns the real-time Resource Shortage Radar, analyzing warehouse inventory
    against SPHERE-standardized humanitarian relief consumption requirements.
    """
    return shortage_radar_service.compute_shortage_radar(db, horizon_days=horizon_days)
