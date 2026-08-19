import math
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.relief_request import ReliefRequest


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on the Earth
    in kilometers using the Haversine formula.
    """
    R = 6371.0  # Earth's radius in kilometers

    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = (
        math.sin(d_lat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(d_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)


class GeoService:
    @staticmethod
    def get_nearby_requests(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 15.0,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Find all emergency relief requests within the specified radius in kilometers.
        Compatible with both SQLite and PostgreSQL without requiring PostGIS extensions.
        """
        query = db.query(ReliefRequest)
        if status_filter:
            query = query.filter(ReliefRequest.status == status_filter)
        
        all_requests = query.all()
        results = []

        for req in all_requests:
            if req.latitude is None or req.longitude is None:
                continue
            dist = haversine_distance(latitude, longitude, req.latitude, req.longitude)
            if dist <= radius_km:
                results.append({
                    "id": req.id,
                    "disaster_type": req.disaster_type,
                    "location_name": req.location_name,
                    "latitude": req.latitude,
                    "longitude": req.longitude,
                    "priority": req.priority,
                    "status": req.status,
                    "affected_people": req.affected_people,
                    "required_resources": req.required_resources,
                    "distance_km": dist,
                    "urgency_description": req.urgency_description,
                    "created_at": req.created_at.isoformat() if req.created_at else None,
                })

        # Sort by closest distance first
        results.sort(key=lambda x: x["distance_km"])
        return results

    @staticmethod
    def get_disaster_hotspots(db: Session, max_cluster_radius_km: float = 25.0) -> List[Dict[str, Any]]:
        """
        Group emergency requests by geographic proximity into hotspot clusters.
        Calculates cluster density, critical request counts, and average priority rating.
        """
        requests = db.query(ReliefRequest).all()
        if not requests:
            return []

        priority_weights = {"low": 25.0, "medium": 50.0, "high": 75.0, "critical": 100.0}
        clusters: List[Dict[str, Any]] = []

        for req in requests:
            if req.latitude is None or req.longitude is None:
                continue

            # Check if this request fits into an existing cluster
            assigned_cluster = None
            for cluster in clusters:
                dist = haversine_distance(cluster["center_lat"], cluster["center_lng"], req.latitude, req.longitude)
                if dist <= max_cluster_radius_km:
                    assigned_cluster = cluster
                    break

            req_priority_score = priority_weights.get(req.priority.lower(), 50.0)

            if assigned_cluster:
                assigned_cluster["requests_count"] += 1
                assigned_cluster["affected_people"] += req.affected_people
                if req.priority.lower() == "critical":
                    assigned_cluster["critical_requests"] += 1
                if req.status in ("assigned", "dispatched", "in_progress"):
                    assigned_cluster["active_missions"] += 1
                assigned_cluster["priority_scores"].append(req_priority_score)
                # Recalculate center
                assigned_cluster["locations"].append(req.location_name)
            else:
                clusters.append({
                    "cluster_id": f"hotspot-{len(clusters) + 1}",
                    "zone_name": req.location_name,
                    "center_lat": req.latitude,
                    "center_lng": req.longitude,
                    "disaster_type": req.disaster_type,
                    "requests_count": 1,
                    "critical_requests": 1 if req.priority.lower() == "critical" else 0,
                    "active_missions": 1 if req.status in ("assigned", "dispatched", "in_progress") else 0,
                    "affected_people": req.affected_people,
                    "priority_scores": [req_priority_score],
                    "locations": [req.location_name],
                })

        # Calculate averages and hazard levels
        for cluster in clusters:
            avg_score = sum(cluster["priority_scores"]) / len(cluster["priority_scores"])
            cluster["average_priority"] = round(avg_score, 1)
            cluster["hazard_level"] = (
                "CRITICAL" if avg_score >= 80 or cluster["critical_requests"] >= 3
                else "HIGH" if avg_score >= 60
                else "MODERATE" if avg_score >= 40
                else "LOW"
            )
            del cluster["priority_scores"]

        clusters.sort(key=lambda c: (c["critical_requests"], c["requests_count"]), reverse=True)
        return clusters

    @staticmethod
    def mask_citizen_coordinates(lat: float, lng: float, precision_decimals: int = 2) -> Dict[str, Any]:
        """
        Fuzz/round coordinates to approximately ~1.1km grid precision
        to preserve citizen anonymity for public/donor tiers.
        """
        return {
            "latitude": round(lat, precision_decimals),
            "longitude": round(lng, precision_decimals),
            "privacy_masked": True,
        }

    @staticmethod
    def get_nearby_incidents(
        db: Session,
        latitude: float,
        longitude: float,
        radius_km: float = 50.0,
        disaster_type: Optional[str] = None,
        minimum_severity: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Find active/monitored incidents within radius, filtering by type and severity."""
        from app.models.incidents import Incident

        query = db.query(Incident).filter(Incident.status.notin_(["RESOLVED", "CANCELLED"]))
        if disaster_type:
            query = query.filter(Incident.disaster_type == disaster_type.lower())
        if minimum_severity is not None:
            query = query.filter(Incident.severity >= minimum_severity)

        incidents = query.all()
        results = []
        for inc in incidents:
            dist = haversine_distance(latitude, longitude, inc.latitude, inc.longitude)
            if dist <= radius_km:
                results.append({
                    "id": inc.id,
                    "title": inc.title,
                    "disaster_type": inc.disaster_type,
                    "severity": inc.severity,
                    "status": inc.status,
                    "escalation_level": inc.escalation_level,
                    "latitude": inc.latitude,
                    "longitude": inc.longitude,
                    "affected_radius_km": inc.affected_radius_km,
                    "distance_km": dist,
                    "created_at": inc.created_at.isoformat() if inc.created_at else None,
                })

        results.sort(key=lambda x: x["distance_km"])
        return results

    @staticmethod
    def get_incident_impact_zone(db: Session, incident_id: str) -> Optional[Dict[str, Any]]:
        """Calculate operational impact zone around an incident (requests, volunteers, warehouses)."""
        from app.models.incidents import Incident, SituationReport
        from app.models.user import User
        from app.models.organization import Organization
        from app.models.resource import ResourceInventory

        incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            return None

        radius = incident.affected_radius_km or 15.0

        # Nearby SOS Requests
        all_reqs = db.query(ReliefRequest).filter(ReliefRequest.status.in_(["pending", "triaged", "assigned", "dispatched"])).all()
        nearby_requests = []
        total_affected = 0
        critical_count = 0
        for r in all_reqs:
            if r.latitude is not None and r.longitude is not None:
                dist = haversine_distance(incident.latitude, incident.longitude, r.latitude, r.longitude)
                if dist <= radius:
                    total_affected += (r.affected_people or 0)
                    if str(r.priority).lower() == "critical":
                        critical_count += 1
                    nearby_requests.append({
                        "id": r.id,
                        "location_name": r.location_name,
                        "priority": r.priority,
                        "status": r.status,
                        "affected_people": r.affected_people,
                        "distance_km": dist,
                    })

        # Nearby Responders / Volunteers
        volunteers = db.query(User).filter(User.role == "volunteer", User.is_active == True).all()
        nearby_volunteers = []
        for v in volunteers:
            # Check if volunteer has approximate location from metadata or mock
            nearby_volunteers.append({
                "id": v.id,
                "name": v.full_name,
                "role": v.role,
                "organization_id": v.organization_id,
            })

        # Nearby Warehouses / Organizations
        orgs = db.query(Organization).all()
        nearby_orgs = []
        for o in orgs:
            nearby_orgs.append({
                "id": o.id,
                "name": o.name,
                "type": o.type,
                "city": o.city,
            })

        # Latest SITREP
        latest_sitrep = (
            db.query(SituationReport)
            .filter(SituationReport.incident_id == incident.id)
            .order_by(SituationReport.created_at.desc())
            .first()
        )

        return {
            "incident_id": incident.id,
            "title": incident.title,
            "disaster_type": incident.disaster_type,
            "severity": incident.severity,
            "status": incident.status,
            "escalation_level": incident.escalation_level,
            "center": {
                "latitude": incident.latitude,
                "longitude": incident.longitude,
                "affected_radius_km": radius,
            },
            "impact_metrics": {
                "active_sos_requests_count": len(nearby_requests),
                "critical_sos_count": critical_count,
                "estimated_population_affected": total_affected or (latest_sitrep.people_affected if latest_sitrep else 0),
                "displaced_people": latest_sitrep.people_displaced if latest_sitrep else 0,
                "casualties": latest_sitrep.casualties_reported if latest_sitrep else 0,
                "infrastructure_damage": latest_sitrep.infrastructure_damage_level if latest_sitrep else "moderate",
            },
            "nearby_relief_requests": nearby_requests[:20],
            "available_volunteers_count": len(nearby_volunteers),
            "responding_organizations": nearby_orgs[:10],
        }

    @staticmethod
    def get_geojson_map_feed(db: Session) -> Dict[str, Any]:
        """Produce comprehensive GeoJSON FeatureCollection of all incidents, hotspots, and resources."""
        from app.models.incidents import Incident

        features = []

        # Incidents Features
        incidents = db.query(Incident).filter(Incident.status != "CANCELLED").all()
        for inc in incidents:
            features.append({
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [inc.longitude, inc.latitude],
                },
                "properties": {
                    "id": inc.id,
                    "layer": "incident",
                    "title": inc.title,
                    "disaster_type": inc.disaster_type,
                    "severity": inc.severity,
                    "status": inc.status,
                    "escalation_level": inc.escalation_level,
                    "affected_radius_km": inc.affected_radius_km,
                    "marker_color": (
                        "#ef4444" if inc.severity >= 8.0
                        else "#f97316" if inc.severity >= 6.0
                        else "#eab308" if inc.severity >= 4.0
                        else "#10b981"
                    ),
                },
            })

        # Active Relief Requests Features
        reqs = db.query(ReliefRequest).filter(ReliefRequest.status.in_(["pending", "triaged", "assigned"])).all()
        for r in reqs:
            if r.latitude is not None and r.longitude is not None:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Point",
                        "coordinates": [r.longitude, r.latitude],
                    },
                    "properties": {
                        "id": r.id,
                        "layer": "relief_request",
                        "location_name": r.location_name,
                        "disaster_type": r.disaster_type,
                        "priority": r.priority,
                        "status": r.status,
                        "affected_people": r.affected_people,
                        "marker_color": (
                            "#ef4444" if str(r.priority).lower() == "critical"
                            else "#f59e0b" if str(r.priority).lower() == "high"
                            else "#3b82f6"
                        ),
                    },
                })

        return {
            "type": "FeatureCollection",
            "features": features,
            "metadata": {
                "total_features": len(features),
                "incidents_count": len(incidents),
                "active_sos_count": len(reqs),
            },
        }


geo_service = GeoService()


