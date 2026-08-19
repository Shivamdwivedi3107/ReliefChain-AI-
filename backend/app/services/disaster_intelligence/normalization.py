from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional


SUPPORTED_DISASTER_TYPES = {
    "flood",
    "earthquake",
    "cyclone",
    "wildfire",
    "landslide",
    "heatwave",
    "storm",
    "tsunami",
    "other",
}


@dataclass
class NormalizedDisasterEvent:
    source: str
    external_id: str
    disaster_type: str
    severity: float
    title: str
    description: Optional[str]
    latitude: float
    longitude: float
    affected_radius_km: float
    started_at: datetime
    status: str = "active"  # active, monitoring, resolved, false_positive
    confidence_score: float = 0.85
    raw_metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "external_id": self.external_id,
            "disaster_type": self.disaster_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "affected_radius_km": self.affected_radius_km,
            "started_at": self.started_at.isoformat() if hasattr(self.started_at, "isoformat") else str(self.started_at),
            "status": self.status,
            "confidence_score": self.confidence_score,
            "raw_metadata": self.raw_metadata,
        }


def normalize_event_payload(payload: Dict[str, Any], default_source: str = "custom_feed") -> NormalizedDisasterEvent:
    """Normalize raw provider data dictionary into standard NormalizedDisasterEvent."""
    d_type = str(payload.get("disaster_type", "other")).lower()
    if d_type not in SUPPORTED_DISASTER_TYPES:
        d_type = "other"

    raw_sev = float(payload.get("severity", 5.0))
    severity = max(1.0, min(10.0, raw_sev))

    lat = float(payload.get("latitude", 0.0))
    lng = float(payload.get("longitude", 0.0))
    # Bounded coordinates
    lat = max(-90.0, min(90.0, lat))
    lng = max(-180.0, min(180.0, lng))

    radius = float(payload.get("affected_radius_km", payload.get("radius_km", 15.0)))
    radius = max(0.5, min(500.0, radius))

    started = payload.get("started_at")
    if isinstance(started, str):
        try:
            started_dt = datetime.fromisoformat(started.replace("Z", "+00:00"))
        except Exception:
            started_dt = datetime.now(timezone.utc)
    elif isinstance(started, datetime):
        started_dt = started
    else:
        started_dt = datetime.now(timezone.utc)

    return NormalizedDisasterEvent(
        source=str(payload.get("source", default_source)),
        external_id=str(payload.get("external_id", payload.get("id", ""))),
        disaster_type=d_type,
        severity=round(severity, 1),
        title=str(payload.get("title", f"{d_type.capitalize()} Incident Alert")),
        description=str(payload.get("description", "")) or None,
        latitude=round(lat, 6),
        longitude=round(lng, 6),
        affected_radius_km=round(radius, 1),
        started_at=started_dt,
        status=str(payload.get("status", "active")),
        confidence_score=round(max(0.1, min(1.0, float(payload.get("confidence_score", 0.85)))), 2),
        raw_metadata=dict(payload.get("raw_metadata") or payload.get("metadata") or {}),
    )
