from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.geo_service import geo_service

router = APIRouter(prefix="/geo", tags=["Geographic Intelligence"])


@router.get("/nearby-requests", summary="Query emergency requests within radius using Haversine calculation")
def get_nearby_relief_requests(
    latitude: float = Query(..., description="Center latitude coordinate", ge=-90.0, le=90.0),
    longitude: float = Query(..., description="Center longitude coordinate", ge=-180.0, le=180.0),
    radius_km: float = Query(15.0, description="Search radius in kilometers", ge=0.5, le=500.0),
    status: Optional[str] = Query(None, description="Optional relief request status filter"),
    db: Session = Depends(get_db),
):
    results = geo_service.get_nearby_requests(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        status_filter=status,
    )
    return {
        "success": True,
        "query": {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
            "status": status,
        },
        "count": len(results),
        "results": results,
    }


@router.get("/disaster-hotspots", summary="Get aggregated emergency clusters and hazard severity ratings")
def get_disaster_hotspots(
    max_cluster_radius_km: float = Query(25.0, description="Clustering radius threshold in km", ge=5.0, le=100.0),
    db: Session = Depends(get_db),
):
    hotspots = geo_service.get_disaster_hotspots(db=db, max_cluster_radius_km=max_cluster_radius_km)
    return {
        "success": True,
        "total_hotspots": len(hotspots),
        "hotspots": hotspots,
    }


@router.get("/incidents/nearby", summary="Search active incidents within geographic radius")
def get_nearby_incidents(
    latitude: float = Query(..., description="Latitude coordinate", ge=-90.0, le=90.0),
    longitude: float = Query(..., description="Longitude coordinate", ge=-180.0, le=180.0),
    radius_km: float = Query(50.0, description="Radius in kilometers", ge=0.5, le=500.0),
    disaster_type: Optional[str] = Query(None, description="Filter by disaster type"),
    minimum_severity: Optional[float] = Query(None, description="Minimum severity threshold", ge=1.0, le=10.0),
    db: Session = Depends(get_db),
):
    results = geo_service.get_nearby_incidents(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        disaster_type=disaster_type,
        minimum_severity=minimum_severity,
    )
    return {
        "success": True,
        "query": {
            "latitude": latitude,
            "longitude": longitude,
            "radius_km": radius_km,
            "disaster_type": disaster_type,
            "minimum_severity": minimum_severity,
        },
        "count": len(results),
        "results": results,
    }


@router.get("/incidents/{incident_id}/impact-zone", summary="Operational impact zone analysis for an incident")
def get_incident_impact_zone(
    incident_id: str,
    db: Session = Depends(get_db),
):
    zone = geo_service.get_incident_impact_zone(db=db, incident_id=incident_id)
    if not zone:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
    return {
        "success": True,
        "impact_zone": zone,
    }


@router.get("/map", summary="GeoJSON map feed of all operational markers and disaster incidents")
def get_geojson_map(db: Session = Depends(get_db)):
    return geo_service.get_geojson_map_feed(db=db)

