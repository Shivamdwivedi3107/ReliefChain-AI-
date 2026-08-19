from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.incidents import Incident, IncidentTimeline
from app.models.user import User


VALID_TRANSITIONS = {
    "DETECTED": {"VERIFIED", "CANCELLED"},
    "VERIFIED": {"ACTIVE", "CANCELLED"},
    "ACTIVE": {"MONITORING", "CONTAINED", "RESOLVED"},
    "MONITORING": {"ACTIVE", "CONTAINED", "RESOLVED"},
    "CONTAINED": {"MONITORING", "RESOLVED"},
    "RESOLVED": set(),
    "CANCELLED": set(),
}


class IncidentService:
    """Service orchestrating incident operations and enforcing strict lifecycle transitions."""

    @staticmethod
    def create_incident(
        db: Session,
        title: str,
        disaster_type: str,
        severity: float,
        latitude: float,
        longitude: float,
        affected_radius_km: float = 10.0,
        event_id: Optional[str] = None,
        organization_id: Optional[str] = None,
        description: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
        actor_id: Optional[str] = None,
    ) -> Incident:
        incident = Incident(
            title=title,
            disaster_type=disaster_type.lower(),
            severity=round(max(1.0, min(10.0, severity)), 1),
            status="DETECTED",
            escalation_level="LEVEL_1_NORMAL",
            latitude=latitude,
            longitude=longitude,
            affected_radius_km=round(affected_radius_km, 1),
            event_id=event_id,
            organization_id=organization_id,
            description=description,
            metadata_json=metadata_json or {},
        )
        db.add(incident)
        db.flush()

        # Add initial detection timeline entry
        timeline = IncidentTimeline(
            incident_id=incident.id,
            event_type="INCIDENT_DETECTED",
            message=f"Incident '{incident.title}' detected with severity {incident.severity}.",
            actor_id=actor_id,
            metadata_json={"disaster_type": incident.disaster_type, "severity": incident.severity},
        )
        db.add(timeline)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def transition_status(
        db: Session,
        incident: Incident,
        target_status: str,
        actor: Optional[User] = None,
        note: Optional[str] = None,
    ) -> Incident:
        current = incident.status.upper()
        target = target_status.upper()

        if current == target:
            return incident

        allowed = VALID_TRANSITIONS.get(current, set())
        if target not in allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid incident lifecycle transition from '{current}' to '{target}'. Allowed target states: {sorted(list(allowed)) or 'None (Terminal state)'}.",
            )

        incident.status = target
        actor_id = actor.id if actor else None

        if target == "VERIFIED" and actor:
            incident.verified_by_user_id = actor.id
        elif target == "RESOLVED" and actor:
            incident.resolved_by_user_id = actor.id

        # Timeline chronicle
        msg = f"Incident state transitioned from {current} to {target}."
        if note:
            msg += f" Note: {note}"

        timeline = IncidentTimeline(
            incident_id=incident.id,
            event_type=f"INCIDENT_{target}",
            message=msg,
            actor_id=actor_id,
            metadata_json={"previous_status": current, "new_status": target, "note": note},
        )
        db.add(timeline)
        db.commit()
        db.refresh(incident)
        return incident

    @staticmethod
    def add_timeline_entry(
        db: Session,
        incident_id: str,
        event_type: str,
        message: str,
        actor_id: Optional[str] = None,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> IncidentTimeline:
        timeline = IncidentTimeline(
            incident_id=incident_id,
            event_type=event_type,
            message=message,
            actor_id=actor_id,
            metadata_json=metadata_json or {},
        )
        db.add(timeline)
        db.commit()
        db.refresh(timeline)
        return timeline

    @classmethod
    def transition_incident(
        cls,
        db: Session,
        incident_id: str,
        target_status: str,
        actor_id: Optional[str] = None,
        note: Optional[str] = None,
    ) -> Incident:
        """Convenience method looking up incident and executing lifecycle transition."""
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incident not found")
        actor = db.query(User).filter(User.id == actor_id).first() if actor_id else None
        return cls.transition_status(db, inc, target_status, actor=actor, note=note)


incident_service = IncidentService()

