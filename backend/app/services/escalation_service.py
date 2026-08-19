from typing import Dict, Any, List
from sqlalchemy.orm import Session
from app.models.incidents import Incident, SituationReport
from app.models.relief_request import ReliefRequest
from app.services.incident_service import incident_service


class DisasterEscalationService:
    """Evaluates multi-factor operational escalation levels for active disaster incidents."""

    @staticmethod
    def calculate_escalation(
        db: Session,
        incident: Incident,
        auto_update_incident: bool = True,
    ) -> Dict[str, Any]:
        reasons: List[str] = []
        score = 0.0

        # 1. Base Severity (1-10) -> Up to 35 points
        sev_points = incident.severity * 3.5
        score += sev_points
        if incident.severity >= 8.0:
            reasons.append(f"Catastrophic disaster severity index ({incident.severity}/10.0)")
        elif incident.severity >= 6.0:
            reasons.append(f"Elevated disaster hazard severity ({incident.severity}/10.0)")

        # 2. Nearby Active Relief Requests / SOS Density -> Up to 25 points
        sos_count = (
            db.query(ReliefRequest)
            .filter(
                ReliefRequest.disaster_type == incident.disaster_type,
                ReliefRequest.status.in_(["pending", "triaged", "assigned"]),
            )
            .count()
        )
        if sos_count >= 20:
            score += 25.0
            reasons.append(f"Critical intake volume ({sos_count} active SOS requests pending)")
        elif sos_count >= 10:
            score += 15.0
            reasons.append(f"High intake volume ({sos_count} active SOS requests pending)")
        elif sos_count >= 3:
            score += 8.0
            reasons.append(f"Active community SOS intake ({sos_count} requests)")

        # 3. Medical Emergency Demands -> Up to 20 points
        medical_sos = (
            db.query(ReliefRequest)
            .filter(
                ReliefRequest.disaster_type == incident.disaster_type,
                ReliefRequest.priority.in_(["Critical", "High"]),
                ReliefRequest.status.in_(["pending", "triaged", "assigned"]),
            )
            .count()
        )
        if medical_sos >= 5:
            score += 20.0
            reasons.append(f"Severe trauma and medical emergencies detected ({medical_sos} critical cases)")
        elif medical_sos >= 1:
            score += 10.0
            reasons.append(f"High-priority emergency aid requests detected ({medical_sos} critical cases)")

        # 4. Situation Reports & Field Casualties -> Up to 20 points
        latest_sitrep = (
            db.query(SituationReport)
            .filter(SituationReport.incident_id == incident.id)
            .order_by(SituationReport.created_at.desc())
            .first()
        )
        if latest_sitrep:
            if latest_sitrep.casualties_reported > 0:
                score += 15.0
                reasons.append(f"Confirmed field casualties ({latest_sitrep.casualties_reported} reported)")
            if latest_sitrep.people_displaced >= 500:
                score += 10.0
                reasons.append(f"Mass displacement ({latest_sitrep.people_displaced} displaced individuals)")
            if latest_sitrep.infrastructure_damage_level in ("severe", "catastrophic"):
                score += 10.0
                reasons.append("Severe/catastrophic infrastructure damage reported")

        # Normalize score
        final_score = int(round(max(0, min(100, score))))

        # Determine level
        if final_score >= 85:
            escalation_level = "LEVEL_4_CRITICAL"
        elif final_score >= 65:
            escalation_level = "LEVEL_3_HIGH"
        elif final_score >= 40:
            escalation_level = "LEVEL_2_ELEVATED"
        else:
            escalation_level = "LEVEL_1_NORMAL"

        if not reasons:
            reasons.append("Baseline operational parameters within nominal thresholds.")

        # Update incident record if requested
        if auto_update_incident and incident.escalation_level != escalation_level:
            old_level = incident.escalation_level
            incident.escalation_level = escalation_level
            db.commit()
            db.refresh(incident)

            incident_service.add_timeline_entry(
                db=db,
                incident_id=incident.id,
                event_type="INCIDENT_ESCALATED",
                message=f"Incident escalation adjusted from {old_level} to {escalation_level} (Score: {final_score}/100).",
                metadata_json={"old_level": old_level, "new_level": escalation_level, "score": final_score},
            )

        return {
            "incident_id": incident.id,
            "incident_title": incident.title,
            "score": final_score,
            "escalation_level": escalation_level,
            "reasons": reasons,
            "decision_support_notice": "Escalation levels are advisory calculations to guide disaster command priority.",
        }

    @classmethod
    def evaluate_incident(cls, db: Session, incident_id: str) -> Dict[str, Any]:
        """Convenience method finding incident and evaluating escalation."""
        inc = db.query(Incident).filter(Incident.id == incident_id).first()
        if not inc:
            return {
                "incident_id": incident_id,
                "escalation_level": "LEVEL_1_NORMAL",
                "score": 0.0,
                "reasons": ["No matching active incident found."],
            }
        return cls.calculate_escalation(db, inc)


escalation_service = DisasterEscalationService()

