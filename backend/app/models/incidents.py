from sqlalchemy import Column, String, Float, Integer, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from app.database import Base
from app.models.base import TimestampMixin, generate_uuid, get_utc_now


class DisasterEvent(Base, TimestampMixin):
    """Normalized ingested disaster event from external or mock feeds."""
    __tablename__ = "disaster_events"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    source = Column(String(50), nullable=False, default="mock_provider", index=True)
    external_id = Column(String(100), nullable=True, index=True)
    disaster_type = Column(String(50), nullable=False, index=True)  # flood, earthquake, cyclone, wildfire, landslide, heatwave, storm, other
    severity = Column(Float, nullable=False, default=5.0, index=True)  # 1.0 - 10.0 scale
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    affected_radius_km = Column(Float, nullable=False, default=15.0)
    started_at = Column(DateTime(timezone=True), nullable=False, default=get_utc_now)
    status = Column(String(30), nullable=False, default="active", index=True)  # active, monitoring, resolved, false_positive
    confidence_score = Column(Float, nullable=False, default=0.85)
    raw_metadata = Column(JSON, nullable=True)

    # Relationships
    incidents = relationship("Incident", back_populates="disaster_event")


class Incident(Base, TimestampMixin):
    """Operational Disaster Incident tracked through strict response lifecycle."""
    __tablename__ = "incidents"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    event_id = Column(String(36), ForeignKey("disaster_events.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    disaster_type = Column(String(50), nullable=False, index=True)
    severity = Column(Float, nullable=False, default=5.0, index=True)
    status = Column(String(30), nullable=False, default="DETECTED", index=True)
    # Lifecycle: DETECTED -> VERIFIED -> ACTIVE -> MONITORING -> CONTAINED -> RESOLVED (or CANCELLED)
    escalation_level = Column(String(30), nullable=False, default="LEVEL_1_NORMAL", index=True)
    # Escalation: LEVEL_1_NORMAL, LEVEL_2_ELEVATED, LEVEL_3_HIGH, LEVEL_4_CRITICAL
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    affected_radius_km = Column(Float, nullable=False, default=10.0)
    verified_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_by_user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    organization_id = Column(String(36), ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    metadata_json = Column(JSON, nullable=True)

    # Relationships
    disaster_event = relationship("DisasterEvent", back_populates="incidents")
    timeline_entries = relationship("IncidentTimeline", back_populates="incident", order_by="IncidentTimeline.created_at.asc()", cascade="all, delete-orphan")
    situation_reports = relationship("SituationReport", back_populates="incident", order_by="SituationReport.created_at.asc()", cascade="all, delete-orphan")


class IncidentTimeline(Base):
    """Append-only audit trail and operational chronicle for an incident."""
    __tablename__ = "incident_timelines"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False, index=True)
    message = Column(String(500), nullable=False)
    actor_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_utc_now, index=True)

    # Relationships
    incident = relationship("Incident", back_populates="timeline_entries")
    actor = relationship("User")


class SituationReport(Base):
    """Structured Situation Report (SITREP) filed by authorized field and command personnel."""
    __tablename__ = "situation_reports"

    id = Column(String(36), primary_key=True, default=generate_uuid, index=True)
    incident_id = Column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    author_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    report_type = Column(String(30), nullable=False, default="field", index=True)  # initial, update, field, final
    summary = Column(Text, nullable=False)
    people_affected = Column(Integer, nullable=False, default=0)
    people_displaced = Column(Integer, nullable=False, default=0)
    casualties_reported = Column(Integer, nullable=False, default=0)
    infrastructure_damage_level = Column(String(20), nullable=False, default="moderate")  # none, low, moderate, severe, catastrophic
    medical_need_level = Column(String(20), nullable=False, default="moderate")  # low, moderate, high, critical
    food_need_level = Column(String(20), nullable=False, default="moderate")  # low, moderate, high, critical
    water_need_level = Column(String(20), nullable=False, default="moderate")  # low, moderate, high, critical
    shelter_need_level = Column(String(20), nullable=False, default="moderate")  # low, moderate, high, critical
    communication_status = Column(String(30), nullable=False, default="operational")  # operational, degraded, offline
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=get_utc_now, index=True)

    # Relationships
    incident = relationship("Incident", back_populates="situation_reports")
    author = relationship("User")
