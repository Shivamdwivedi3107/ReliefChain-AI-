"""
ReliefChain AI — Volunteer Intelligent Assignment & Recommendation Engine
Calculates multi-criteria matching scores (distance, skill affinity, active workload, reliability)
to assist field coordinators with optimal volunteer dispatch.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.relief_request import ReliefRequest
from app.services.geo_service import haversine_distance
from app.services.ai_explainability import ai_explainability
from app.core.logging import logger


class VolunteerMatchingService:
    """
    Intelligent decision-support engine recommending best-fit volunteers for emergency missions.
    """

    @staticmethod
    def calculate_volunteer_match(
        volunteer: User,
        target_lat: float,
        target_lng: float,
        required_skills: List[str],
        active_missions_count: int = 0,
    ) -> Dict[str, Any]:
        """
        Calculates individual volunteer multi-factor matching score (0 to 100).
        """
        vol_lat = volunteer.current_latitude or target_lat
        vol_lng = volunteer.current_longitude or target_lng

        # 1. Proximity Distance Score (0 to 100, 35% weight)
        dist_km = haversine_distance(vol_lat, vol_lng, target_lat, target_lng)
        # 0km = 100, 50km+ = 0
        distance_score = max(0.0, min(100.0, 100.0 - (dist_km * 2.0)))

        # 2. Skill Affinity Score (0 to 100, 30% weight)
        vol_skills = [s.lower().strip() for s in (volunteer.skills or [])]
        req_skills_clean = [s.lower().strip() for s in required_skills]
        matched_skills = [s for s in req_skills_clean if s in vol_skills]

        if not req_skills_clean:
            skill_score = 80.0
        elif matched_skills:
            skill_score = min(100.0, (len(matched_skills) / len(req_skills_clean)) * 100.0)
        else:
            skill_score = 40.0 if vol_skills else 25.0

        # 3. Workload Capacity Score (0 to 100, 20% weight)
        max_capacity = max(1, volunteer.max_mission_capacity or 3)
        available_slots = max(0, max_capacity - active_missions_count)
        workload_score = (available_slots / max_capacity) * 100.0

        # 4. Reliability & Verification Score (0 to 100, 15% weight)
        reliability = volunteer.reliability_score or 4.5  # 1.0 to 5.0
        rel_score = min(100.0, (reliability / 5.0) * 100.0)

        # Composite Weighted Score
        match_score = (
            (distance_score * 0.35)
            + (skill_score * 0.30)
            + (workload_score * 0.20)
            + (rel_score * 0.15)
        )
        match_score = round(match_score, 1)

        # Recommendation Category
        if match_score >= 80.0 and available_slots > 0:
            rec_tag = "HIGHLY_RECOMMENDED"
        elif match_score >= 55.0 and available_slots > 0:
            rec_tag = "RECOMMENDED"
        else:
            rec_tag = "CONSIDER_IF_NEEDED"

        xai = ai_explainability.explain_volunteer_match(
            match_score=match_score,
            distance_km=dist_km,
            skill_score=skill_score,
            workload_score=workload_score,
            matched_skills=matched_skills,
        )

        return {
            "volunteer_id": volunteer.id,
            "volunteer_name": volunteer.full_name,
            "email": volunteer.email,
            "phone_number": volunteer.phone_number,
            "match_score": match_score,
            "distance_km": round(dist_km, 2),
            "distance_score": round(distance_score, 1),
            "skill_score": round(skill_score, 1),
            "workload_score": round(workload_score, 1),
            "reliability_score": round(rel_score, 1),
            "active_missions": active_missions_count,
            "max_capacity": max_capacity,
            "matched_skills": matched_skills,
            "recommendation": rec_tag,
            "explanation": xai["rationale_bullets"],
        }

    @classmethod
    def get_recommendations_for_mission(
        cls,
        db: Session,
        mission_id: str,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Finds and ranks all active volunteers for a specific relief request mission.
        """
        mission = db.query(ReliefRequest).filter(ReliefRequest.id == mission_id).first()
        if not mission:
            return {
                "success": False,
                "error": f"Mission '{mission_id}' not found.",
                "recommendations": [],
            }

        target_lat = mission.latitude or 28.6139
        target_lng = mission.longitude or 77.2090

        # Infer required skills from disaster type and resources
        required_skills: List[str] = []
        if mission.disaster_type in ("earthquake", "landslide"):
            required_skills.extend(["search_and_rescue", "trauma", "first_aid"])
        elif mission.disaster_type in ("flood", "tsunami", "cyclone"):
            required_skills.extend(["water_rescue", "logistics", "first_aid"])
        else:
            required_skills.extend(["first_aid", "logistics", "distribution"])

        # Fetch available volunteers
        volunteers = db.query(User).filter(
            User.role == "volunteer",
            User.is_active == True,
            User.availability == True,
        ).all()

        scored_candidates = []
        for vol in volunteers:
            # Count currently active missions assigned to this volunteer
            active_count = db.query(ReliefRequest).filter(
                ReliefRequest.assigned_volunteer_id == vol.id,
                ReliefRequest.status.in_(["assigned", "dispatched", "in_progress"]),
            ).count()

            scored = cls.calculate_volunteer_match(
                volunteer=vol,
                target_lat=target_lat,
                target_lng=target_lng,
                required_skills=required_skills,
                active_missions_count=active_count,
            )
            scored_candidates.append(scored)

        # Sort descending by match score
        scored_candidates.sort(key=lambda x: x["match_score"], reverse=True)
        top_recommendations = scored_candidates[:limit]

        return {
            "success": True,
            "mission_id": mission.id,
            "disaster_type": mission.disaster_type,
            "location_name": mission.location_name,
            "priority": mission.priority,
            "required_skills": required_skills,
            "total_volunteers_evaluated": len(volunteers),
            "recommendations": top_recommendations,
            "dss_disclaimer": "Recommendations are generated by the Volunteer Matching Engine. Dispatchers retain final assignment authority.",
        }

    @classmethod
    def match_volunteers_for_mission(
        cls,
        db: Session,
        mission_id: str,
        limit: int = 5,
    ) -> List[Dict[str, Any]]:
        """Convenience helper returning list of ranked volunteer match profiles."""
        res = cls.get_recommendations_for_mission(db, mission_id, limit)
        recs = res.get("recommendations", [])
        return [
            {
                "volunteer_id": r["volunteer_id"],
                "full_name": r["volunteer_name"],
                "match_score": r["match_score"],
                "match_reasons": r.get("explanation") or ["Skill affinity", "Proximity"],
            }
            for r in recs
        ]


volunteer_matching_service = VolunteerMatchingService()
volunteer_matcher = volunteer_matching_service

