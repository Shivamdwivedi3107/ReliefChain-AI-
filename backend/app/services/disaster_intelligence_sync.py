from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.incidents import DisasterEvent, Incident, IncidentTimeline
from app.models.audit_log import AuditLog
from app.services.disaster_intelligence import provider_registry
from app.services.incident_service import incident_service


class DisasterIntelligenceSyncService:
    """Synchronizes external feeds, ingests disaster events, and auto-provisions incidents."""

    @staticmethod
    async def sync_provider(
        db: Session,
        provider_name: str = "mock_provider",
        auto_create_incidents: bool = True,
        actor_id: str = None,
    ) -> Dict[str, Any]:
        provider = provider_registry.get_provider(provider_name)
        if not provider:
            return {
                "success": False,
                "error": f"Disaster provider '{provider_name}' not found.",
                "available_providers": provider_registry.list_providers(),
            }

        normalized_events = await provider.fetch_events()
        new_events_count = 0
        updated_events_count = 0
        incidents_created_count = 0

        for norm in normalized_events:
            existing = (
                db.query(DisasterEvent)
                .filter(
                    DisasterEvent.source == norm.source,
                    DisasterEvent.external_id == norm.external_id,
                )
                .first()
            )

            if existing:
                # Update existing disaster event
                existing.severity = norm.severity
                existing.title = norm.title
                existing.description = norm.description
                existing.latitude = norm.latitude
                existing.longitude = norm.longitude
                existing.affected_radius_km = norm.affected_radius_km
                existing.status = norm.status
                existing.confidence_score = norm.confidence_score
                existing.raw_metadata = norm.raw_metadata
                updated_events_count += 1
                event_record = existing
            else:
                # Create new disaster event
                event_record = DisasterEvent(
                    source=norm.source,
                    external_id=norm.external_id,
                    disaster_type=norm.disaster_type,
                    severity=norm.severity,
                    title=norm.title,
                    description=norm.description,
                    latitude=norm.latitude,
                    longitude=norm.longitude,
                    affected_radius_km=norm.affected_radius_km,
                    started_at=norm.started_at,
                    status=norm.status,
                    confidence_score=norm.confidence_score,
                    raw_metadata=norm.raw_metadata,
                )
                db.add(event_record)
                db.flush()
                new_events_count += 1

            # Auto-provision operational incident for high/critical events if not already linked
            if auto_create_incidents:
                linked_incident = db.query(Incident).filter(Incident.event_id == event_record.id).first()
                if not linked_incident:
                    new_inc = incident_service.create_incident(
                        db=db,
                        title=f"[FEED ALERT] {event_record.title}",
                        disaster_type=event_record.disaster_type,
                        severity=event_record.severity,
                        latitude=event_record.latitude,
                        longitude=event_record.longitude,
                        affected_radius_km=event_record.affected_radius_km,
                        event_id=event_record.id,
                        description=event_record.description,
                        metadata_json={"feed_source": norm.source, "external_id": norm.external_id},
                        actor_id=actor_id,
                    )
                    incidents_created_count += 1

        # Audit log
        audit = AuditLog(
            user_id=actor_id,
            action="DISASTER_INTELLIGENCE_SYNC",
            entity_type="disaster_feed",
            entity_id=provider_name,
            details_json={
                "provider": provider_name,
                "events_fetched": len(normalized_events),
                "new_events": new_events_count,
                "updated_events": updated_events_count,
                "incidents_created": incidents_created_count,
            },
        )
        db.add(audit)
        db.commit()

        return {
            "success": True,
            "provider": provider_name,
            "events_fetched": len(normalized_events),
            "new_events": new_events_count,
            "updated_events": updated_events_count,
            "incidents_created": incidents_created_count,
            "notice": "Disaster intelligence events ingested and synchronized successfully.",
        }


disaster_sync_service = DisasterIntelligenceSyncService()
