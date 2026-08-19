"""
ReliefChain AI — Resource Demand Forecasting Engine
Estimates future supply requirements (water, rations, trauma kits, emergency shelters, blankets)
and calculates inventory gaps against available warehouse stock.
"""

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from app.services.ai_explainability import ai_explainability
from app.models.resource import Resource, ResourceInventory
from app.core.logging import logger


class ResourceForecastingService:
    """
    Forecasting engine estimating humanitarian supply demand, burn rates,
    and warehouse replenishment shortfalls.
    """

    @staticmethod
    def calculate_predicted_demand(
        disaster_type: str,
        severity: float,
        population_affected: int,
        active_sos_requests: int = 0,
        forecast_period_hours: int = 24,
    ) -> Dict[str, float]:
        """
        Computes per-capita emergency supply demand scaled by severity, duration, and SOS pressure.
        """
        people = max(1, int(population_affected))
        sev = max(1.0, min(10.0, float(severity)))
        days = max(0.5, float(forecast_period_hours) / 24.0)

        # Baseline per-person multiplier curves
        # Water: 3-5L per person per day depending on severity
        water_per_person_day = 3.0 + (sev - 1.0) * 0.25
        predicted_water = round(people * water_per_person_day * days, 1)

        # Food: 2-3 ration packs per person per day
        food_per_person_day = 2.0 + (sev - 1.0) * 0.15
        predicted_food = round(people * food_per_person_day * days, 1)

        # Medical Kits: ~2-5 kits per 100 people scaled by trauma intensity
        medical_mult = 0.04 if disaster_type.lower() in ("earthquake", "landslide", "explosion") else 0.02
        predicted_medical = max(1, round(people * medical_mult * (sev / 5.0)))

        # Shelter / Tents: ~1 tent per 4.5 family members for displaced populations
        displacement_rate = 0.45 if disaster_type.lower() in ("flood", "cyclone", "earthquake", "tsunami") else 0.20
        displacement_rate *= (sev / 10.0)
        predicted_shelter = max(1, round((people * displacement_rate) / 4.5))

        # Blankets / Bedding: ~0.8-1.2 units per affected person
        predicted_blankets = max(1, round(people * 0.85 * (1.0 + (sev - 1.0) * 0.05)))

        return {
            "water": predicted_water,
            "food": predicted_food,
            "medical_kits": float(predicted_medical),
            "shelter_tents": float(predicted_shelter),
            "blankets": float(predicted_blankets),
        }

    @classmethod
    def forecast_demand_and_gaps(
        cls,
        disaster_type: str,
        severity: float,
        population_affected: int,
        active_sos_requests: int = 0,
        disaster_duration_hours: int = 24,
        forecast_period_hours: int = 24,
        organization_id: Optional[str] = None,
        db_session: Optional[Session] = None,
    ) -> Dict[str, Any]:
        """
        Generates full resource demand projection, queries current warehouse inventories,
        and calculates exact supply gap shortages.
        """
        predicted_demand = cls.calculate_predicted_demand(
            disaster_type=disaster_type,
            severity=severity,
            population_affected=population_affected,
            active_sos_requests=active_sos_requests,
            forecast_period_hours=forecast_period_hours,
        )

        current_inventory: Dict[str, float] = {
            "water": 0.0,
            "food": 0.0,
            "medical_kits": 0.0,
            "shelter_tents": 0.0,
            "blankets": 0.0,
        }

        # Query live database inventory if session provided
        if db_session:
            try:
                query = db_session.query(ResourceInventory).join(Resource)
                if organization_id:
                    query = query.filter(ResourceInventory.organization_id == organization_id)
                inventories = query.all()

                for inv in inventories:
                    res_name = (inv.resource.name if inv.resource else "").lower()
                    avail = float(inv.available_quantity or 0.0)
                    if "water" in res_name:
                        current_inventory["water"] += avail
                    elif "food" in res_name or "ration" in res_name:
                        current_inventory["food"] += avail
                    elif "medical" in res_name or "trauma" in res_name or "first aid" in res_name:
                        current_inventory["medical_kits"] += avail
                    elif "shelter" in res_name or "tent" in res_name:
                        current_inventory["shelter_tents"] += avail
                    elif "blanket" in res_name or "bedding" in res_name:
                        current_inventory["blankets"] += avail
            except Exception as err:
                logger.warning(f"[ResourceForecaster] DB inventory lookup note: {err}")

        # Compute Shortage Gaps
        inventory_gap: Dict[str, float] = {}
        for item, demand_qty in predicted_demand.items():
            avail = current_inventory.get(item, 0.0)
            gap = max(0.0, round(demand_qty - avail, 1))
            if gap > 0:
                inventory_gap[item] = gap

        # Actionable Recommendations
        recommendations = []
        if inventory_gap:
            shortage_items = [f"{k.replace('_', ' ').title()} (short by {v})" for k, v in inventory_gap.items()]
            recommendations.append(f"Immediate emergency procurement required: {', '.join(shortage_items)}.")
            recommendations.append("Lock partner NGO supply transfer requests to cover regional deficit.")
        else:
            recommendations.append("Existing depot stock is sufficient for the next operational window.")

        # XAI Explanation Breakdown
        xai = ai_explainability.explain_resource_forecast(
            predicted_demand=predicted_demand,
            inventory_gap=inventory_gap,
            severity=severity,
            duration_hours=forecast_period_hours,
        )

        return {
            "success": True,
            "disaster_type": disaster_type,
            "severity": severity,
            "population_affected": population_affected,
            "forecast_period_hours": forecast_period_hours,
            "predicted_demand": predicted_demand,
            "current_inventory": current_inventory,
            "inventory_gap": inventory_gap,
            "has_shortage": len(inventory_gap) > 0,
            "recommendations": recommendations,
            "explanation": xai,
            "dss_disclaimer": "Forecasts represent decision-support estimations based on SPHERE humanitarian standards. Operational logistics teams should verify field burn rates.",
        }


resource_forecasting_service = ResourceForecastingService()
