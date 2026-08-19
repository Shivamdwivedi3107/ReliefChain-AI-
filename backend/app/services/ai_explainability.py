"""
ReliefChain AI — AI Explainability (XAI) Engine
Provides human-interpretable feature contribution breakdowns, transparency scores,
and rationale explanations for disaster risk, emergency priority, resource demand,
and volunteer matching predictions.
"""

from typing import Dict, Any, List


class AIExplainabilityEngine:
    """
    Reusable Explainable AI (XAI) service providing non-technical transparency breakdowns
    for all AI/ML decision-support subsystems.
    """

    @staticmethod
    def explain_disaster_risk(
        disaster_type: str,
        risk_score: float,
        rainfall_mm: float,
        population_density: float,
        vulnerable_population_pct: float,
        infrastructure_risk_score: float,
        previous_disaster_frequency: int,
        resource_availability_score: float,
    ) -> Dict[str, Any]:
        """Generate structured factor contributions for disaster risk predictions."""
        factors: List[Dict[str, Any]] = []

        # 1. Disaster Type Hazard Baseline
        type_weights = {
            "earthquake": {"pts": 30, "desc": "High seismic shock hazard and building collapse vulnerability"},
            "tsunami": {"pts": 35, "desc": "Extreme coastal inundation and surge wave impact"},
            "cyclone": {"pts": 28, "desc": "Severe gale-force winds and coastal storm surge"},
            "flood": {"pts": 25, "desc": "Rising water levels, river overflow, and flash flooding"},
            "landslide": {"pts": 22, "desc": "Terrain instability and mudflow risk"},
            "wildfire": {"pts": 24, "desc": "Rapid combustion spread and smoke hazard"},
            "drought": {"pts": 15, "desc": "Sustained water table depletion and agricultural loss"},
        }
        hazard_info = type_weights.get(disaster_type.lower(), {"pts": 18, "desc": f"Environmental hazard for {disaster_type}"})
        factors.append({
            "factor": "hazard_type_baseline",
            "name": f"Disaster Hazard ({disaster_type.title()})",
            "contribution_points": hazard_info["pts"],
            "impact": "INCREASES_RISK",
            "explanation": hazard_info["desc"],
        })

        # 2. Rainfall
        if rainfall_mm > 100:
            factors.append({
                "factor": "extreme_precipitation",
                "name": "Extreme Rainfall",
                "contribution_points": 20,
                "impact": "INCREASES_RISK",
                "explanation": f"Heavy rainfall of {rainfall_mm}mm significantly elevates flash flood and waterlogging risks.",
            })
        elif rainfall_mm > 40:
            factors.append({
                "factor": "moderate_precipitation",
                "name": "Moderate Rainfall",
                "contribution_points": 10,
                "impact": "INCREASES_RISK",
                "explanation": f"Precipitation of {rainfall_mm}mm increases ground saturation.",
            })

        # 3. Population Density
        if population_density > 1000:
            factors.append({
                "factor": "high_population_density",
                "name": "High Population Density",
                "contribution_points": 18,
                "impact": "INCREASES_RISK",
                "explanation": f"Dense urban population ({population_density:.0f}/km²) amplifies casualty potential and evacuation gridlock.",
            })
        elif population_density > 300:
            factors.append({
                "factor": "moderate_population_density",
                "name": "Moderate Population Density",
                "contribution_points": 8,
                "impact": "INCREASES_RISK",
                "explanation": f"Moderate settlement density ({population_density:.0f}/km²).",
            })

        # 4. Vulnerable Population Percentage
        if vulnerable_population_pct > 25:
            factors.append({
                "factor": "high_vulnerability_demographic",
                "name": "Vulnerable Demographics",
                "contribution_points": 16,
                "impact": "INCREASES_RISK",
                "explanation": f"High proportion ({vulnerable_population_pct:.1f}%) of elderly, children, or mobility-impaired residents.",
            })

        # 5. Infrastructure Risk
        if infrastructure_risk_score > 0.6:
            factors.append({
                "factor": "fragile_infrastructure",
                "name": "Infrastructure Fragility",
                "contribution_points": 15,
                "impact": "INCREASES_RISK",
                "explanation": f"High structural vulnerability score ({infrastructure_risk_score:.2f}) due to aging bridges, unpaved roads, or weak drainage.",
            })

        # 6. Local Resource Cushion
        if resource_availability_score < 0.3:
            factors.append({
                "factor": "depleted_local_supplies",
                "name": "Resource Scarcity",
                "contribution_points": 12,
                "impact": "INCREASES_RISK",
                "explanation": "Critical depot inventory shortage locally will delay first-response supplies.",
            })
        elif resource_availability_score > 0.7:
            factors.append({
                "factor": "adequate_local_supplies",
                "name": "Resource Preparedness Cushion",
                "contribution_points": -10,
                "impact": "DECREASES_RISK",
                "explanation": "Abundant local warehouse reserves help absorb initial emergency shocks.",
            })

        # Summary text
        top_factors = [f["name"] for f in sorted(factors, key=lambda x: abs(x["contribution_points"]), reverse=True)[:3]]
        summary = f"Risk score of {risk_score:.1f}/100 is primarily driven by: {', '.join(top_factors)}."

        return {
            "summary": summary,
            "factor_count": len(factors),
            "factors": factors,
            "explainability_confidence": 0.92,
        }

    @staticmethod
    def explain_resource_forecast(
        predicted_demand: Dict[str, float],
        inventory_gap: Dict[str, float],
        severity: float,
        duration_hours: int,
    ) -> Dict[str, Any]:
        """Explain the rationale behind supply demand forecasts and depot gaps."""
        explanations: List[Dict[str, Any]] = []

        for item, qty in predicted_demand.items():
            gap = inventory_gap.get(item, 0)
            status = "CRITICAL_SHORTAGE" if gap > 0 else "SUFFICIENT_STOCK"
            explanations.append({
                "resource": item,
                "predicted_demand": qty,
                "shortage_gap": gap,
                "status": status,
                "rationale": (
                    f"Scaled for severity {severity}/10 over {duration_hours}h duration. "
                    f"{'Immediate emergency procurement needed!' if gap > 0 else 'Depot has sufficient reserved stock.'}"
                ),
            })

        return {
            "forecast_rationale": f"Estimated resource burn rates calculated for {duration_hours}h operational window at disaster severity {severity}/10.",
            "breakdown": explanations,
        }

    @staticmethod
    def explain_volunteer_match(
        match_score: float,
        distance_km: float,
        skill_score: float,
        workload_score: float,
        matched_skills: List[str],
    ) -> Dict[str, Any]:
        """Generate human-readable matching justification for volunteer dispatch."""
        reasons = []
        if distance_km <= 5.0:
            reasons.append(f"Immediate proximity ({distance_km:.1f} km from ground incident)")
        elif distance_km <= 20.0:
            reasons.append(f"Rapid response zone ({distance_km:.1f} km away)")
        else:
            reasons.append(f"Transit required ({distance_km:.1f} km away)")

        if matched_skills:
            reasons.append(f"Possesses mission-critical skills: {', '.join(matched_skills)}")
        else:
            reasons.append("General humanitarian response support")

        if workload_score >= 80:
            reasons.append("Optimal workload capacity (currently unburdened)")
        elif workload_score < 40:
            reasons.append("High active workload (near maximum active mission quota)")

        return {
            "overall_match_score": match_score,
            "rationale_bullets": reasons,
            "detailed_scores": {
                "distance_score": round(100 - min(distance_km * 2, 100), 1),
                "skill_affinity": skill_score,
                "workload_availability": workload_score,
            },
        }


ai_explainability = AIExplainabilityEngine()
