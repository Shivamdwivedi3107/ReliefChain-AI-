from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.relief_request import ReliefRequest
from app.services.geo_service import haversine_distance


class VolunteerRecommendationEngine:
    @staticmethod
    def get_recommendations_for_mission(
        db: Session,
        mission_id: str,
        max_results: int = 10,
    ) -> Dict[str, Any]:
        """
        Rank and recommend available field volunteers for a disaster relief mission.
        Evaluates distance, skill affinity, availability, active mission workload, and reliability.
        Does NOT automatically assign the volunteer; output is purely advisory for human dispatchers.
        """
        mission = db.query(ReliefRequest).filter(ReliefRequest.id == mission_id).first()
        if not mission:
            return {"error": "Mission not found", "recommendations": []}

        # Query all active volunteer users
        volunteers = db.query(User).filter(
            User.role == "volunteer",
            User.is_active == True,
        ).all()

        if not volunteers:
            return {
                "mission_id": mission.id,
                "disaster_type": mission.disaster_type,
                "location_name": mission.location_name,
                "recommendations": [],
            }

        # Identify required skill keywords from mission payload
        required_skills = set()
        req_resources_str = str(mission.required_resources or "").lower()
        urgency_str = (mission.urgency_description or "").lower()
        combined_text = f"{req_resources_str} {urgency_str} {mission.disaster_type.lower()}"

        if "medical" in combined_text or "trauma" in combined_text or "injur" in combined_text:
            required_skills.add("medical")
            required_skills.add("first_aid")
        if "rescue" in combined_text or "trapped" in combined_text or "flood" in combined_text or "earthquake" in combined_text:
            required_skills.add("rescue")
        if "transport" in combined_text or "vehicle" in combined_text or "boat" in combined_text:
            required_skills.add("transport")
        if "food" in combined_text or "water" in combined_text or "ration" in combined_text:
            required_skills.add("logistics")
        if "shelter" in combined_text or "blanket" in combined_text or "tarpaulin" in combined_text:
            required_skills.add("shelter")

        if not required_skills:
            required_skills = {"logistics", "first_aid"}

        scored_candidates: List[Dict[str, Any]] = []

        for v in volunteers:
            # 1. Distance Calculation
            v_lat = v.current_latitude if v.current_latitude is not None else (mission.latitude or 28.6139)
            v_lng = v.current_longitude if v.current_longitude is not None else (mission.longitude or 77.2090)
            
            dist_km = haversine_distance(v_lat, v_lng, mission.latitude or 28.6139, mission.longitude or 77.2090)
            
            # Distance Score: 100 at 0km, down to 0 at 50km
            distance_score = max(0.0, 100.0 - (dist_km * 2.0))

            # 2. Availability Score
            availability_score = 100.0 if getattr(v, "availability", True) else 0.0

            # 3. Skill Match
            v_skills = set(getattr(v, "skills", []) or ["first_aid", "logistics"])
            matched_skills = v_skills.intersection(required_skills)
            skill_score = (len(matched_skills) / len(required_skills)) * 100.0 if required_skills else 100.0
            skill_score = min(100.0, skill_score)

            # 4. Workload Capacity
            active_missions_count = (
                db.query(ReliefRequest)
                .filter(
                    ReliefRequest.assigned_volunteer_id == v.id,
                    ReliefRequest.status.in_(["assigned", "dispatched", "in_progress"]),
                )
                .count()
            )
            max_cap = getattr(v, "max_mission_capacity", 3) or 3
            if active_missions_count >= max_cap:
                workload_score = 0.0
            else:
                workload_score = ((max_cap - active_missions_count) / max_cap) * 100.0

            # 5. Reliability Score
            reliability_score = float(getattr(v, "reliability_score", 95.0) or 95.0)

            # Weighted Aggregate Score (0 to 100)
            final_score = (
                (distance_score * 0.30)
                + (skill_score * 0.25)
                + (availability_score * 0.20)
                + (workload_score * 0.15)
                + (reliability_score * 0.10)
            )

            scored_candidates.append({
                "volunteer_id": v.id,
                "volunteer_name": v.full_name,
                "email": v.email,
                "phone_number": v.phone_number,
                "score": round(final_score, 1),
                "distance_km": dist_km,
                "skill_match": round(skill_score, 1),
                "matched_skills": list(matched_skills),
                "availability_score": round(availability_score, 1),
                "workload_score": round(workload_score, 1),
                "active_missions": active_missions_count,
                "max_capacity": max_cap,
                "reliability_score": round(reliability_score, 1),
            })

        # Sort descending by recommendation score
        scored_candidates.sort(key=lambda x: x["score"], reverse=True)

        return {
            "mission_id": mission.id,
            "disaster_type": mission.disaster_type,
            "location_name": mission.location_name,
            "priority": mission.priority,
            "required_skills": list(required_skills),
            "recommendations": scored_candidates[:max_results],
        }


recommendation_engine = VolunteerRecommendationEngine()
