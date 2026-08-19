"""
ReliefChain AI — Disaster Risk Prediction Engine
Hybrid rule-based and machine-learning risk scoring service for assessing environmental,
demographic, and infrastructural disaster hazards.
"""

from typing import Dict, Any, List, Optional
from app.services.ai_explainability import ai_explainability
from app.core.logging import logger


class DisasterRiskPredictionService:
    """
    Hybrid Disaster Risk Estimator providing automated vulnerability,
    precipitation, and hazard level classifications.
    """

    @staticmethod
    def calculate_rule_based_risk(
        disaster_type: str,
        historical_severity: float = 5.0,
        rainfall_mm: float = 0.0,
        temperature_c: float = 25.0,
        population_density: float = 500.0,
        vulnerable_population_pct: float = 15.0,
        infrastructure_risk_score: float = 0.5,
        previous_disaster_frequency: int = 1,
        resource_availability_score: float = 0.5,
    ) -> float:
        """
        Layer 1: Deterministic Multi-Factor Disaster Risk Scoring (0 to 100).
        """
        score = 0.0

        # 1. Disaster Hazard Baseline (Max 25 pts)
        hazard_map = {
            "earthquake": 25.0,
            "tsunami": 25.0,
            "cyclone": 22.0,
            "flood": 20.0,
            "landslide": 18.0,
            "wildfire": 20.0,
            "drought": 14.0,
        }
        score += hazard_map.get(disaster_type.lower(), 15.0)

        # 2. Historical Severity (Max 20 pts)
        # historical_severity is 1-10
        norm_severity = max(1.0, min(10.0, float(historical_severity)))
        score += (norm_severity / 10.0) * 20.0

        # 3. Meteorological & Environmental Shock (Max 15 pts)
        if rainfall_mm > 150:
            score += 15.0
        elif rainfall_mm > 75:
            score += 10.0
        elif rainfall_mm > 30:
            score += 5.0

        if temperature_c > 42.0 or temperature_c < -10.0:
            score += 5.0

        # 4. Demographic & Population Vulnerability (Max 20 pts)
        # Population density points (Max 10 pts)
        if population_density > 1500:
            score += 10.0
        elif population_density > 500:
            score += 6.0
        elif population_density > 100:
            score += 3.0

        # Vulnerable population percentage points (Max 10 pts)
        vulnerable_clamped = max(0.0, min(100.0, float(vulnerable_population_pct)))
        score += (vulnerable_clamped / 100.0) * 10.0

        # 5. Infrastructure Fragility & Recurrence (Max 15 pts)
        infra_clamped = max(0.0, min(1.0, float(infrastructure_risk_score)))
        score += infra_clamped * 10.0

        if previous_disaster_frequency >= 3:
            score += 5.0
        elif previous_disaster_frequency >= 1:
            score += 2.5

        # 6. Local Resource Cushion Offset (-10 to +10 pts)
        res_clamped = max(0.0, min(1.0, float(resource_availability_score)))
        score += (1.0 - res_clamped) * 10.0

        return float(max(5.0, min(100.0, round(score, 1))))

    @classmethod
    def predict_risk(
        cls,
        disaster_type: str,
        historical_severity: float = 5.0,
        rainfall_mm: float = 0.0,
        temperature_c: float = 25.0,
        population_density: float = 500.0,
        vulnerable_population_pct: float = 15.0,
        infrastructure_risk_score: float = 0.5,
        previous_disaster_frequency: int = 1,
        resource_availability_score: float = 0.5,
        location_name: str = "",
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Calculates hybrid disaster risk, risk level, confidence, explainability,
        and operational recommendations.
        """
        # Step 1: Compute baseline deterministic risk score
        risk_score = cls.calculate_rule_based_risk(
            disaster_type=disaster_type,
            historical_severity=historical_severity,
            rainfall_mm=rainfall_mm,
            temperature_c=temperature_c,
            population_density=population_density,
            vulnerable_population_pct=vulnerable_population_pct,
            infrastructure_risk_score=infrastructure_risk_score,
            previous_disaster_frequency=previous_disaster_frequency,
            resource_availability_score=resource_availability_score,
        )

        # Step 2: Determine categorical tier
        if risk_score >= 80.0:
            risk_level = "CRITICAL"
        elif risk_score >= 60.0:
            risk_level = "HIGH"
        elif risk_score >= 35.0:
            risk_level = "MODERATE"
        else:
            risk_level = "LOW"

        confidence = 0.88 if risk_score > 50 else 0.92

        # Step 3: Generate Explainability Analysis
        xai_breakdown = ai_explainability.explain_disaster_risk(
            disaster_type=disaster_type,
            risk_score=risk_score,
            rainfall_mm=rainfall_mm,
            population_density=population_density,
            vulnerable_population_pct=vulnerable_population_pct,
            infrastructure_risk_score=infrastructure_risk_score,
            previous_disaster_frequency=previous_disaster_frequency,
            resource_availability_score=resource_availability_score,
        )

        # Step 4: Formulate Actionable Directives & Recommendations
        recommendations = []
        if risk_level == "CRITICAL":
            recommendations.extend([
                "Initiate immediate pre-emptive civilian evacuation in low-lying / vulnerable zones.",
                "Mobilize rapid medical trauma squads and pre-position clean water filtration units.",
                "Activate mutual aid coordination across regional NGO partner networks.",
            ])
        elif risk_level == "HIGH":
            recommendations.extend([
                "Alert emergency volunteer brigades and place warehouse dispatch depots on standby.",
                "Issue public weather and emergency advisory notices via local broadcasts.",
                "Pre-allocate emergency ration packs and inflatable shelter kits.",
            ])
        elif risk_level == "MODERATE":
            recommendations.extend([
                "Monitor meteorological telemetry and river catchment sensors closely.",
                "Verify warehouse inventory levels and test communication relays.",
            ])
        else:
            recommendations.extend([
                "Maintain standard situational monitoring and routine volunteer standby.",
            ])

        return {
            "success": True,
            "disaster_type": disaster_type.lower(),
            "location_name": location_name or "Target Zone",
            "coordinates": {"latitude": latitude, "longitude": longitude} if latitude is not None and longitude is not None else None,
            "risk_score": risk_score,
            "risk_level": risk_level,
            "confidence": confidence,
            "risk_factors": xai_breakdown["factors"],
            "explanation_summary": xai_breakdown["summary"],
            "recommendations": recommendations,
            "model_version": "v1.0.0-hybrid-dss",
            "dss_disclaimer": "ReliefChain AI Risk Predictor is an advisory decision support system. Ground coordinators must verify real-time situational observations.",
        }


risk_prediction_service = DisasterRiskPredictionService()
