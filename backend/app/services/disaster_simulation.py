"""
ReliefChain AI — Disaster Impact Simulation Engine
Admin-level simulation sandbox modeling hypothetical disaster scenarios, casualty projections,
volunteer mobilization demands, and logistics burn rates for contingency planning.
"""

from typing import Dict, Any, List


class DisasterSimulationService:
    """
    Simulation engine for modeling macro humanitarian impacts and contingency load testing.
    """

    @staticmethod
    def run_simulation(
        disaster_type: str,
        severity: float,
        population_affected: int,
        duration_hours: int = 48,
        location_name: str = "Simulated Incident Sector",
        scenario_title: str = "Hypothetical Scenario",
    ) -> Dict[str, Any]:
        """
        Executes a deterministic multi-variable impact simulation.
        """
        people = max(10, int(population_affected))
        sev = max(1.0, min(10.0, float(severity)))
        duration = max(6, int(duration_hours))

        # 1. Projected SOS Request Intake Volume
        # Intensity curve based on severity and population
        sos_rate_factor = 0.08 if disaster_type.lower() in ("earthquake", "tsunami") else 0.05
        sos_rate_factor *= (sev / 5.0)
        projected_sos_total = max(5, round(people * sos_rate_factor))
        peak_hourly_sos = max(2, round(projected_sos_total / (duration * 0.35)))

        # 2. Casualty & Trauma Projections
        casualty_rate = 0.035 * (sev / 5.0) if disaster_type.lower() in ("earthquake", "landslide") else 0.015 * (sev / 5.0)
        estimated_casualties = max(1, round(people * casualty_rate))
        critical_trauma_cases = max(1, round(estimated_casualties * 0.30))

        # 3. Volunteer Mobilization Demands
        # Ratio of ~1 field volunteer per 40-70 affected individuals
        volunteers_needed = max(4, round(people / (65.0 - (sev * 2.5))))
        medical_volunteers = max(1, round(volunteers_needed * 0.30))
        logistics_volunteers = max(2, round(volunteers_needed * 0.45))
        general_volunteers = max(1, volunteers_needed - (medical_volunteers + logistics_volunteers))

        # 4. Resource Burn Rates
        daily_multiplier = duration / 24.0
        total_water_liters = round(people * (3.5 + sev * 0.2) * daily_multiplier, 1)
        total_food_rations = round(people * (2.0 + sev * 0.1) * daily_multiplier, 1)
        total_medical_kits = max(2, round(people * 0.025 * (sev / 5.0)))
        total_emergency_tents = max(1, round((people * 0.35 * (sev / 10.0)) / 4.5))

        # 5. Composite Risk & Response Severity Tier
        if sev >= 8.0 or people > 10000:
            sim_risk_level = "CRITICAL"
        elif sev >= 5.5 or people > 2500:
            sim_risk_level = "HIGH"
        else:
            sim_risk_level = "MODERATE"

        # Strategic Contingency Recommendations
        action_directives = [
            f"Pre-position minimum {total_water_liters:,.0f} Liters potable water and {total_food_rations:,.0f} food rations.",
            f"Mobilize response battalion of {volunteers_needed} field personnel ({medical_volunteers} medical, {logistics_volunteers} logistics).",
            f"Establish triage intake center prepared for ~{critical_trauma_cases} priority trauma cases.",
            f"Ensure {total_emergency_tents} temporary shelter structures are allocated in safe secondary staging areas.",
        ]

        return {
            "success": True,
            "scenario_title": scenario_title,
            "disaster_type": disaster_type,
            "severity": sev,
            "population_affected": people,
            "duration_hours": duration,
            "location_name": location_name,
            "simulation_mode": "DECISION_SUPPORT_SIMULATION_ONLY",
            "projected_impact": {
                "total_sos_requests": projected_sos_total,
                "peak_hourly_sos_rate": peak_hourly_sos,
                "estimated_casualties": estimated_casualties,
                "critical_trauma_cases": critical_trauma_cases,
                "simulation_risk_level": sim_risk_level,
            },
            "personnel_requirements": {
                "total_volunteers_needed": volunteers_needed,
                "medical_specialists": medical_volunteers,
                "logistics_handlers": logistics_volunteers,
                "general_field_responders": general_volunteers,
            },
            "supply_requirements": {
                "water_liters": total_water_liters,
                "food_rations": total_food_rations,
                "medical_kits": total_medical_kits,
                "shelter_tents": total_emergency_tents,
            },
            "contingency_directives": action_directives,
            "dss_disclaimer": "This output is a simulated scenario model produced for humanitarian emergency contingency planning and training. It does not reflect real-time live sensor data.",
        }


disaster_simulation_service = DisasterSimulationService()
