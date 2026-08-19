import random
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.relief_request import ReliefRequest
from app.models.user import User
from app.services.notification_service import notification_manager
from app.core.logging import logger

SIMULATED_SCENARIOS = {
    "cyclone_landing": {
        "title": "Cyclone Vardah Category-4 Landfall",
        "disaster_type": "cyclone",
        "locations": [
            {"name": "Sector 4 Coastal Fishery Zone", "lat": 13.0827, "lng": 80.2707, "affected": 45, "priority": "critical"},
            {"name": "Marina Beach Flood Relief Shelter", "lat": 13.0500, "lng": 80.2824, "affected": 20, "priority": "high"},
            {"name": "Velachery Low-Lying Inundation Pocket", "lat": 12.9815, "lng": 80.2180, "affected": 12, "priority": "medium"},
        ],
    },
    "earthquake_swarm": {
        "title": "Magnitude 6.8 Structural Collapse Swarm",
        "disaster_type": "earthquake",
        "locations": [
            {"name": "Old Town Commercial Complex Block B", "lat": 28.6562, "lng": 77.2410, "affected": 60, "priority": "critical"},
            {"name": "Metro Bridge Pillar 14 Underpass", "lat": 28.6139, "lng": 77.2090, "affected": 15, "priority": "high"},
            {"name": "Residential Sector 12 Evacuation Camp", "lat": 28.5355, "lng": 77.3910, "affected": 8, "priority": "low"},
        ],
    },
}


class DisasterSimulationEngine:
    def __init__(self):
        self.is_running: bool = False
        self.active_scenario: Optional[str] = None
        self.simulated_count: int = 0
        self.started_at: Optional[datetime] = None

    def start_simulation(self, db: Session, scenario_key: str = "cyclone_landing") -> Dict[str, Any]:
        scenario = SIMULATED_SCENARIOS.get(scenario_key, SIMULATED_SCENARIOS["cyclone_landing"])
        self.is_running = True
        self.active_scenario = scenario["title"]
        self.started_at = datetime.now(timezone.utc)

        # Get or pick a demo citizen for ownership
        demo_citizen = db.query(User).filter(User.role == "citizen").first()
        citizen_id = demo_citizen.id if demo_citizen else "demo-simulated-citizen"

        created_simulated_requests = []
        for loc in scenario["locations"]:
            sim_req = ReliefRequest(
                citizen_id=citizen_id,
                disaster_type=scenario["disaster_type"],
                location_name=f"[SIMULATED] {loc['name']}",
                latitude=loc["lat"],
                longitude=loc["lng"],
                affected_people=loc["affected"],
                priority=loc["priority"],
                status="pending",
                is_simulated=True,
                urgency_description=f"Automated disaster scenario injection: {scenario['title']}. Structural collapse and waterlogging reported.",
                required_resources=[{"item": "emergency trauma kits", "qty": 10}, {"item": "potable water rations", "qty": 50}],
            )
            db.add(sim_req)
            created_simulated_requests.append(sim_req)

        db.commit()
        for req in created_simulated_requests:
            db.refresh(req)

        self.simulated_count += len(created_simulated_requests)

        # Trigger real-time alert
        logger.info(f"Disaster Simulation started: {scenario['title']} ({len(created_simulated_requests)} emergencies injected).")
        return {
            "status": "active",
            "is_running": True,
            "scenario": scenario["title"],
            "injected_requests_count": len(created_simulated_requests),
            "simulated_request_ids": [r.id for r in created_simulated_requests],
            "started_at": self.started_at.isoformat(),
        }

    def stop_simulation(self, db: Session, purge_simulated_data: bool = True) -> Dict[str, Any]:
        purged = 0
        if purge_simulated_data:
            purged = db.query(ReliefRequest).filter(ReliefRequest.is_simulated == True).delete()
            db.commit()

        self.is_running = False
        scenario_name = self.active_scenario
        self.active_scenario = None
        self.started_at = None

        logger.info(f"Disaster Simulation stopped. Purged {purged} simulated records.")
        return {
            "status": "stopped",
            "is_running": False,
            "scenario": scenario_name,
            "purged_records_count": purged,
        }

    def get_status(self) -> Dict[str, Any]:
        return {
            "is_running": self.is_running,
            "active_scenario": self.active_scenario,
            "total_simulated_events": self.simulated_count,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "available_scenarios": list(SIMULATED_SCENARIOS.keys()),
        }


simulation_engine = DisasterSimulationEngine()
