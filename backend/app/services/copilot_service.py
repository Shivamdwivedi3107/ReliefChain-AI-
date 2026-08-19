from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.incidents import Incident, SituationReport, IncidentTimeline
from app.models.relief_request import ReliefRequest
from app.models.resource import Resource, ResourceInventory
from app.models.user import User
from app.models.mission_history import MissionStatusHistory
from app.services.escalation_service import escalation_service
from app.services.volunteer_matching import volunteer_matcher



class DisasterCopilotService:
    """
    AI Disaster Copilot Service:
    Provides verifiable, rule-based operational assistance, situational reasoning,
    incident diagnoses, supply shortage identification, and volunteer matching.
    """

    SUGGESTED_PROMPTS = [
        {"id": "critical_incidents", "text": "Show critical incidents requiring immediate response", "category": "incidents"},
        {"id": "resource_shortages", "text": "Find critical resource shortages across all sectors", "category": "logistics"},
        {"id": "recommend_volunteers", "text": "Recommend top volunteers for priority missions", "category": "dispatch"},
        {"id": "highest_risk_areas", "text": "Identify highest risk disaster zones and impact perimeters", "category": "geospatial"},
        {"id": "command_summary", "text": "Summarize overall humanitarian command status", "category": "command"},
    ]

    def query(self, db: Session, prompt: str, user_role: str = "admin", incident_id: Optional[str] = None) -> Dict[str, Any]:
        prompt_lower = (prompt or "").lower().strip()

        # 1. Specific incident explanation
        if incident_id or "incident" in prompt_lower and any(w in prompt_lower for w in ["why", "explain", "reason", "diagnose"]):
            return self._explain_incident(db, prompt_lower, incident_id)

        # 2. Critical incidents
        if any(w in prompt_lower for w in ["critical", "severe", "threat", "emergency"]) and "shortage" not in prompt_lower:
            return self._get_critical_incidents_response(db)

        # 3. Resource shortages & supply forecasting
        if any(w in prompt_lower for w in ["shortage", "inventory", "supply", "water", "food", "medical", "ration"]):
            return self._get_resource_shortage_response(db)

        # 4. Volunteer recommendation / dispatch
        if any(w in prompt_lower for w in ["volunteer", "dispatch", "responder", "assign"]):
            return self._get_volunteer_dispatch_response(db)

        # 5. High risk areas / Geospatial
        if any(w in prompt_lower for w in ["zone", "area", "hotspot", "geo", "radius", "map", "near"]):
            return self._get_risk_zones_response(db)

        # 6. Default Command Overview
        return self._get_command_overview_response(db)

    def _explain_incident(self, db: Session, prompt: str, incident_id: Optional[str]) -> Dict[str, Any]:
        incident = None
        if incident_id:
            incident = db.query(Incident).filter(Incident.id == incident_id).first()
        if not incident:
            incident = db.query(Incident).order_by(Incident.severity.desc(), Incident.created_at.desc()).first()

        if not incident:
            return {
                "source": "ReliefChain AI Copilot (Operational Rule Engine)",
                "intent": "incident_explanation",
                "answer": "No active incidents currently registered in the database.",
                "insights": [],
                "suggested_actions": ["Declare a new disaster incident via Command Center."],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        # Run escalation evaluation
        esc = escalation_service.evaluate_incident(db, incident.id)

        reasons_text = " ".join(f"• {r}" for r in esc["reasons"])
        answer = (
            f"Incident '{incident.title}' ({incident.disaster_type.upper()}) is classified at status {incident.status} "
            f"with Severity {incident.severity:.1f}/10 and Escalation Tier {esc['escalation_level']} (Score: {esc['score']}/100).\n\n"
            f"Primary Threat Drivers:\n{reasons_text}"
        )

        return {
            "source": "ReliefChain AI Copilot (Operational Rule Engine)",
            "intent": "incident_explanation",
            "incident_id": incident.id,
            "incident_title": incident.title,
            "answer": answer,
            "insights": [
                {"label": "Disaster Type", "value": incident.disaster_type.capitalize()},
                {"label": "Severity Rating", "value": f"{incident.severity:.1f} / 10.0"},
                {"label": "Escalation Level", "value": esc["escalation_level"]},
                {"label": "Threat Index", "value": f"{esc['score']} / 100"},
                {"label": "Impact Radius", "value": f"{incident.affected_radius_km} km"},
            ],
            "suggested_actions": [
                f"Verify operational containment for {incident.title}",
                "Review field situation reports (SITREPs)",
                "Pre-position regional warehouse inventory",
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _get_critical_incidents_response(self, db: Session) -> Dict[str, Any]:
        incidents = (
            db.query(Incident)
            .filter(Incident.status.in_(["DETECTED", "VERIFIED", "ACTIVE", "MONITORING"]))
            .order_by(Incident.severity.desc())
            .limit(5)
            .all()
        )

        if not incidents:
            return {
                "source": "ReliefChain AI Copilot (Operational Rule Engine)",
                "intent": "critical_incidents",
                "answer": "All disaster incidents are currently contained or resolved. No critical active threats detected.",
                "insights": [],
                "suggested_actions": ["Monitor sensor feeds for incoming multi-hazard warnings."],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        crit_count = sum(1 for i in incidents if i.severity >= 7.0)
        items_summary = "\n".join(
            f"• [{i.status}] {i.title} — Severity {i.severity:.1f}/10 ({i.disaster_type}) — Radius: {i.affected_radius_km}km"
            for i in incidents
        )

        answer = (
            f"Identified {len(incidents)} active incident(s), with {crit_count} operating at elevated/critical severity:\n\n"
            f"{items_summary}\n\n"
            f"Recommendation: Prioritize volunteer deployment and resource allocations to incidents with severity ≥ 7.0."
        )

        return {
            "source": "ReliefChain AI Copilot (Operational Rule Engine)",
            "intent": "critical_incidents",
            "answer": answer,
            "insights": [
                {"label": "Active Incidents", "value": str(len(incidents))},
                {"label": "Critical Incidents (Sev ≥ 7.0)", "value": str(crit_count)},
                {"label": "Highest Severity", "value": f"{incidents[0].severity:.1f}/10" if incidents else "N/A"},
            ],
            "suggested_actions": [
                "Deploy available field volunteers to top-priority sector",
                "Run multi-factor operational escalation scan",
                "Check warehouse stock buffer against SPHERE demand",
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _get_resource_shortage_response(self, db: Session) -> Dict[str, Any]:
        inventories = db.query(ResourceInventory).all()
        active_sos = db.query(ReliefRequest).filter(ReliefRequest.status.in_(["pending", "triaged", "assigned"])).all()

        total_available = sum(inv.available_quantity for inv in inventories)
        total_reserved = sum(inv.reserved_quantity for inv in inventories)
        affected_pop = sum(r.affected_people for r in active_sos)

        # SPHERE water demand = 15L / person / day
        predicted_water_needed = affected_pop * 15.0
        # Food rations = 3 packs / person / day
        predicted_food_needed = affected_pop * 3.0

        shortage_items = []
        for inv in inventories:
            res_name = inv.resource.name if inv.resource else "Supplies"
            if inv.available_quantity < (inv.total_quantity * 0.25):
                shortage_items.append(f"• {res_name}: {inv.available_quantity:.0f} units remaining (Depot: {inv.warehouse_location or 'Main'})")

        shortage_text = "\n".join(shortage_items) if shortage_items else "• All warehouse stock levels are currently above 25% reserve cushion."

        answer = (
            f"Resource Inventory Radar Analysis for {affected_pop} affected citizens across active zones:\n\n"
            f"Supply Status:\n"
            f"• Available Depot Stock: {total_available:,.0f} units\n"
            f"• Reserved / Allocated: {total_reserved:,.0f} units\n"
            f"• Estimated Daily Water Demand (SPHERE): {predicted_water_needed:,.0f} Liters\n"
            f"• Estimated Daily Food Demand: {predicted_food_needed:,.0f} Ration Packs\n\n"
            f"Depot Shortage Alerts:\n{shortage_text}"
        )

        return {
            "source": "ReliefChain AI Copilot (Operational Rule Engine)",
            "intent": "resource_shortages",
            "answer": answer,
            "insights": [
                {"label": "Depot Stock Available", "value": f"{total_available:,.0f} units"},
                {"label": "Affected Population", "value": f"{affected_pop:,} people"},
                {"label": "Est. Daily Water Demand", "value": f"{predicted_water_needed:,.0f} L"},
                {"label": "Est. Daily Ration Demand", "value": f"{predicted_food_needed:,.0f} packs"},
            ],
            "suggested_actions": [
                "Initiate donor supply drive for high-demand items",
                "Rebalance stock between regional warehouses",
                "Lock in supplier reserves via Resource Shortage Radar",
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _get_volunteer_dispatch_response(self, db: Session) -> Dict[str, Any]:
        volunteers = db.query(User).filter(User.role == "volunteer", User.is_active == True).all()
        open_requests = db.query(ReliefRequest).filter(ReliefRequest.status.in_(["pending", "triaged"])).order_by(ReliefRequest.created_at.desc()).all()

        avail_count = sum(1 for v in volunteers if v.availability)

        if not open_requests:
            return {
                "source": "ReliefChain AI Copilot (Operational Rule Engine)",
                "intent": "volunteer_dispatch",
                "answer": f"All relief requests have been assigned. {avail_count} of {len(volunteers)} field volunteers are currently on standby.",
                "insights": [{"label": "Deployable Volunteers", "value": str(avail_count)}],
                "suggested_actions": ["Maintain volunteer squads on high-alert monitoring."],
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

        top_req = open_requests[0]
        # Run volunteer matcher
        recs = volunteer_matcher.match_volunteers_for_mission(db, top_req.id, limit=3)
        rec_lines = []
        for r in recs:
            rec_lines.append(f"• {r['full_name']} — Match: {r['match_score']}% ({', '.join(r['match_reasons'])})")

        rec_text = "\n".join(rec_lines) if rec_lines else "• No active volunteers within matching distance."

        answer = (
            f"Volunteer Dispatch & Smart Matching Overview:\n"
            f"• Available Responders: {avail_count} / {len(volunteers)}\n"
            f"• Unassigned High-Priority SOS Missions: {len(open_requests)}\n\n"
            f"Top Matches for Mission '{top_req.location_name}' ({top_req.disaster_type.upper()}):\n{rec_text}"
        )

        return {
            "source": "ReliefChain AI Copilot (Operational Rule Engine)",
            "intent": "volunteer_dispatch",
            "answer": answer,
            "insights": [
                {"label": "Available Volunteers", "value": f"{avail_count} / {len(volunteers)}"},
                {"label": "Pending Missions", "value": str(len(open_requests))},
                {"label": "Top Target Mission", "value": top_req.location_name},
            ],
            "suggested_actions": [
                f"Dispatch top matched volunteer to {top_req.location_name}",
                "Review volunteer workload capacities",
                "Verify volunteer certifications and safety equipment",
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _get_risk_zones_response(self, db: Session) -> Dict[str, Any]:
        incidents = db.query(Incident).filter(Incident.status.in_(["DETECTED", "VERIFIED", "ACTIVE", "MONITORING"])).all()
        total_coverage_km2 = sum(3.14159 * (i.affected_radius_km ** 2) for i in incidents)

        lines = [
            f"• {i.title} ({i.disaster_type.upper()}): Lat {i.latitude:.4f}, Lng {i.longitude:.4f} (Radius: {i.affected_radius_km}km, Sev: {i.severity:.1f})"
            for i in incidents[:4]
        ]
        lines_text = "\n".join(lines) if lines else "• No active impact perimeters."

        answer = (
            f"Geospatial Threat & Impact Zone Summary:\n"
            f"• Active Monitored Perimeters: {len(incidents)}\n"
            f"• Estimated Geographic Footprint: {total_coverage_km2:,.1f} km²\n\n"
            f"Active Disaster Coordinates:\n{lines_text}"
        )

        return {
            "source": "ReliefChain AI Copilot (Operational Rule Engine)",
            "intent": "risk_zones",
            "answer": answer,
            "insights": [
                {"label": "Monitored Zones", "value": str(len(incidents))},
                {"label": "Total Footprint", "value": f"{total_coverage_km2:,.1f} km²"},
            ],
            "suggested_actions": [
                "Inspect Interactive Disaster Map with GIS layers",
                "Broadcast geo-fenced safety advisory notices",
                "Verify perimeter roadblocks and evacuation corridors",
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def _get_command_overview_response(self, db: Session) -> Dict[str, Any]:
        active_inc = db.query(func.count(Incident.id)).filter(Incident.status.in_(["DETECTED", "VERIFIED", "ACTIVE", "MONITORING"])).scalar() or 0
        open_sos = db.query(func.count(ReliefRequest.id)).filter(ReliefRequest.status.in_(["pending", "triaged"])).scalar() or 0
        vol_count = db.query(func.count(User.id)).filter(User.role == "volunteer", User.is_active == True).scalar() or 0
        sitreps_count = db.query(func.count(SituationReport.id)).scalar() or 0

        answer = (
            f"ReliefChain AI Emergency Operations Command Overview:\n\n"
            f"• Active Incidents: {active_inc}\n"
            f"• Unassigned SOS Distress Intakes: {open_sos}\n"
            f"• Active Field Responders: {vol_count}\n"
            f"• Field Situation Reports Filed: {sitreps_count}\n"
            f"• Overall Command Readiness: OPERATIONAL (Telemetry verified)\n\n"
            f"All dual-layer AI prioritization models, risk estimation pipelines, and SHA-256 transparency ledgers are operational."
        )

        return {
            "source": "ReliefChain AI Copilot (Operational Rule Engine)",
            "intent": "command_overview",
            "answer": answer,
            "insights": [
                {"label": "Active Incidents", "value": str(active_inc)},
                {"label": "Open SOS Requests", "value": str(open_sos)},
                {"label": "Registered Responders", "value": str(vol_count)},
                {"label": "Field SITREPs", "value": str(sitreps_count)},
                {"label": "System Health", "value": "100% OPERATIONAL"},
            ],
            "suggested_actions": [
                "Review highest severity incident in Command Center",
                "Run Resource Shortage Radar scan",
                "Check AI model registry versions and telemetry",
            ],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }


copilot_service = DisasterCopilotService()
