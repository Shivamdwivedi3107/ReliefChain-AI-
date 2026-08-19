from typing import Dict, Any, List
from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session

from app.models.incidents import Incident, SituationReport, IncidentTimeline
from app.models.disaster import Disaster
from app.models.relief_request import ReliefRequest
from app.models.user import User
from app.models.organization import Organization
from app.services.incident_service import incident_service


class DemoScenarioService:
    """
    Demo Scenario Suite:
    Provides pre-packaged multi-hazard disaster emergency datasets for presentations,
    hackathons, and college project evaluation.
    """

    SCENARIOS = {
        "flood_cyclone_crisis": {
            "title": "Cyclone & Flash Flood Surge (Category 4)",
            "hazard_type": "cyclone",
            "severity": 8.8,
            "population_affected": 12500,
            "location_name": "Coastal Bay Delta Sector 4",
            "latitude": 21.6500,
            "longitude": 87.5200,
            "radius_km": 45.0,
            "description": "Category 4 tropical cyclone landfall accompanied by a 4.5m storm surge and rapid river overflow. Low-lying communities stranded with critical freshwater contamination.",
            "sos_templates": [
                {"title": "Delta Village East", "people": 120, "priority": "Critical", "needs": {"water": 500, "medical": 20}, "urgency": "Flooding up to roof level. 15 elderly citizens stranded."},
                {"title": "Bridge Approach Camp", "people": 350, "priority": "Critical", "needs": {"food": 1000, "water": 1200}, "urgency": "Access highway submerged. Rations exhausted."},
                {"title": "Fishermen Colony", "people": 85, "priority": "High", "needs": {"shelter": 15, "medical": 10}, "urgency": "Boats destroyed. Need dry shelter tarpaulins."},
            ],
            "sitrep": {
                "report_type": "field",
                "summary": "Storm surge breaching secondary dykes. 4 bridges impassable. Air drops requested.",
                "casualties": 4,
                "displaced": 3200,
                "damage_level": "catastrophic",
            }
        },
        "seismic_emergency": {
            "title": "Magnitude 7.4 Major Earthquake Emergency",
            "hazard_type": "earthquake",
            "severity": 9.3,
            "population_affected": 24000,
            "location_name": "Mountain Valley Urban Center",
            "latitude": 34.0837,
            "longitude": 74.7973,
            "radius_km": 60.0,
            "description": "Severe shallow crustal earthquake resulting in high-density structural collapse, major arterial road blockage, and trauma casualties.",
            "sos_templates": [
                {"title": "Central Hospital Perimeter", "people": 450, "priority": "Critical", "needs": {"medical": 100, "blankets": 300}, "urgency": "ER wing damaged. Emergency trauma surgery triage set up outdoors."},
                {"title": "Residential Block 9", "people": 210, "priority": "Critical", "needs": {"water": 600, "shelter": 40}, "urgency": "Multi-story building collapsed. Active search and rescue in progress."},
                {"title": "Transit Hub Camp", "people": 580, "priority": "High", "needs": {"food": 1500, "water": 2000}, "urgency": "Displaced transit passengers sleeping in open grounds."},
            ],
            "sitrep": {
                "report_type": "medical",
                "summary": "Over 200 trauma cases reported in first 3 hours. Severe blood and suture shortage.",
                "casualties": 18,
                "displaced": 8500,
                "damage_level": "catastrophic",
            }
        },
        "wildfire_evacuation": {
            "title": "Fast-Moving Forest & Scrub Wildfire",
            "hazard_type": "wildfire",
            "severity": 7.8,
            "population_affected": 6500,
            "location_name": "Pine Ridge Foothills & Valley",
            "latitude": 13.0827,
            "longitude": 80.2707,
            "radius_km": 30.0,
            "description": "Rapidly spreading brush and forest wildfire driven by 40-knot winds. Dense smoke cover and mandatory evacuation orders across 3 subdivisions.",
            "sos_templates": [
                {"title": "Pine Ridge School Evacuation Center", "people": 310, "priority": "High", "needs": {"blankets": 250, "water": 800, "food": 600}, "urgency": "Temporary shelter at full capacity. Heavy smoke inhalation cases."},
                {"title": "North Ridge Highway Exit", "people": 90, "priority": "Critical", "needs": {"medical": 30, "water": 200}, "urgency": "Vehicles trapped by fallen trees and burning brush."},
            ],
            "sitrep": {
                "report_type": "containment",
                "summary": "Containment line holding at 35%. Fire approaching eastern utility substation.",
                "casualties": 1,
                "displaced": 1850,
                "damage_level": "severe",
            }
        },
    }

    def list_scenarios(self) -> List[Dict[str, Any]]:
        return [
            {
                "key": k,
                "title": v["title"],
                "hazard_type": v["hazard_type"],
                "severity": v["severity"],
                "population_affected": v["population_affected"],
                "location_name": v["location_name"],
                "description": v["description"],
            }
            for k, v in self.SCENARIOS.items()
        ]

    def load_scenario(self, db: Session, scenario_key: str, actor_user: Optional[User] = None) -> Dict[str, Any]:
        if scenario_key not in self.SCENARIOS:
            scenario_key = "flood_cyclone_crisis"

        sc = self.SCENARIOS[scenario_key]

        # 1. Create or ensure Disaster Incident
        inc = incident_service.create_incident(
            db=db,
            title=sc["title"],
            disaster_type=sc["hazard_type"],
            severity=sc["severity"],
            latitude=sc["latitude"],
            longitude=sc["longitude"],
            affected_radius_km=sc["radius_km"],
            description=sc["description"],
        )

        # Transition incident to ACTIVE state for demo
        incident_service.transition_incident(db, inc.id, "VERIFIED", actor_id=actor_user.id if actor_user else None, note="Verified via Satellite Multi-Hazard Feed")
        incident_service.transition_incident(db, inc.id, "ACTIVE", actor_id=actor_user.id if actor_user else None, note="Emergency response protocol activated")

        # 2. Get or create citizen reporter for SOS requests
        citizen = db.query(User).filter(User.role == "citizen").first()
        if not citizen:
            citizen = db.query(User).first()

        created_sos_count = 0
        if citizen:
            for item in sc["sos_templates"]:
                req = ReliefRequest(
                    citizen_id=citizen.id,
                    disaster_type=sc["hazard_type"],
                    location_name=item["title"],
                    latitude=sc["latitude"] + 0.01,
                    longitude=sc["longitude"] + 0.01,
                    affected_people=item["people"],
                    required_resources=item["needs"],
                    urgency_description=item["urgency"],
                    priority=item["priority"],
                    status="pending",
                    ai_predicted_priority=item["priority"],
                    ai_confidence=0.92,
                )
                db.add(req)
                created_sos_count += 1

        # 3. Add Situation Report
        sitrep_data = sc["sitrep"]
        sitrep = SituationReport(
            incident_id=inc.id,
            author_id=actor_user.id if actor_user else (citizen.id if citizen else None),
            report_type=sitrep_data["report_type"],
            summary=sitrep_data["summary"],
            casualties_reported=sitrep_data["casualties"],
            people_displaced=sitrep_data["displaced"],
            infrastructure_damage_level=sitrep_data["damage_level"],
        )
        db.add(sitrep)
        db.commit()

        return {
            "success": True,
            "scenario_key": scenario_key,
            "scenario_title": sc["title"],
            "incident_id": inc.id,
            "severity": sc["severity"],
            "sos_requests_created": created_sos_count,
            "sitrep_submitted": True,
            "message": f"Demo scenario '{sc['title']}' loaded successfully into real-time operational state.",
            "loaded_at": datetime.now(timezone.utc).isoformat(),
        }


demo_scenario_service = DemoScenarioService()
