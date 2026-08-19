from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.resource import Resource, ResourceInventory
from app.models.relief_request import ReliefRequest
from app.models.incidents import Incident


class ResourceShortageRadarService:
    """
    Resource Shortage Radar Engine:
    Cross-references warehouse depot inventories with SPHERE humanitarian demand projections
    to detect real-time supply imbalances and compute color-coded replenishment directives.
    """

    # SPHERE daily standard consumption per person
    SPHERE_BENCHMARKS = {
        "water": {"unit": "Liters", "daily_per_person": 15.0, "critical_buffer_days": 3},
        "food": {"unit": "Ration Packs", "daily_per_person": 3.0, "critical_buffer_days": 3},
        "medical": {"unit": "Trauma Kits", "daily_per_person": 0.05, "critical_buffer_days": 5},
        "shelter": {"unit": "Tents / Kits", "daily_per_person": 0.20, "critical_buffer_days": 7},
        "blankets": {"unit": "Thermal Blankets", "daily_per_person": 1.0, "critical_buffer_days": 3},
        "hygiene": {"unit": "Kits", "daily_per_person": 0.10, "critical_buffer_days": 5},
    }

    def compute_shortage_radar(self, db: Session, horizon_days: int = 3) -> Dict[str, Any]:
        # 1. Total affected population across active SOS requests & incidents
        active_sos = db.query(ReliefRequest).filter(
            ReliefRequest.status.in_(["pending", "triaged", "assigned", "in_progress"])
        ).all()
        total_affected_pop = sum(r.affected_people for r in active_sos)
        if total_affected_pop == 0:
            total_affected_pop = 100  # Baseline minimum for demonstration

        # 2. Inventory by category
        inventories = db.query(ResourceInventory).all()
        stock_by_category: Dict[str, float] = {}
        for inv in inventories:
            cat = (inv.resource.category if inv.resource else "general").lower()
            stock_by_category[cat] = stock_by_category.get(cat, 0.0) + inv.available_quantity

        # Also map specific resource names to categories
        for inv in inventories:
            if inv.resource:
                name_lower = inv.resource.name.lower()
                if "water" in name_lower and "water" not in stock_by_category:
                    stock_by_category["water"] = stock_by_category.get("water", 0.0) + inv.available_quantity
                elif ("food" in name_lower or "ration" in name_lower) and "food" not in stock_by_category:
                    stock_by_category["food"] = stock_by_category.get("food", 0.0) + inv.available_quantity
                elif ("medical" in name_lower or "trauma" in name_lower) and "medical" not in stock_by_category:
                    stock_by_category["medical"] = stock_by_category.get("medical", 0.0) + inv.available_quantity
                elif ("tent" in name_lower or "shelter" in name_lower) and "shelter" not in stock_by_category:
                    stock_by_category["shelter"] = stock_by_category.get("shelter", 0.0) + inv.available_quantity
                elif "blanket" in name_lower and "blankets" not in stock_by_category:
                    stock_by_category["blankets"] = stock_by_category.get("blankets", 0.0) + inv.available_quantity

        radar_items: List[Dict[str, Any]] = []
        critical_shortage_count = 0
        warning_shortage_count = 0

        for cat_key, benchmark in self.SPHERE_BENCHMARKS.items():
            daily_rate = benchmark["daily_per_person"]
            required_demand = total_affected_pop * daily_rate * horizon_days
            available_stock = stock_by_category.get(cat_key, 0.0)

            ratio = (available_stock / required_demand) if required_demand > 0 else 1.0
            gap = max(0.0, required_demand - available_stock)

            if ratio >= 1.25:
                status_code = "GREEN"
                status_label = "STABLE"
                urgency = "LOW"
                recommendation = "Maintain regular buffer stock replenishment."
            elif ratio >= 0.80:
                status_code = "YELLOW"
                status_label = "MONITOR"
                urgency = "MODERATE"
                recommendation = f"Stock adequate for ~{(available_stock / (total_affected_pop * daily_rate)):.1f} days. Monitor incoming intakes."
                warning_shortage_count += 1
            elif ratio >= 0.40:
                status_code = "ORANGE"
                status_label = "SHORTAGE_RISK"
                urgency = "HIGH"
                recommendation = f"Allocate {gap:,.0f} additional {benchmark['unit']} to prevent imminent stockout."
                warning_shortage_count += 1
            else:
                status_code = "RED"
                status_label = "CRITICAL_SHORTAGE"
                urgency = "CRITICAL"
                recommendation = f"URGENT: Expedite procurement/dispatch of {gap:,.0f} {benchmark['unit']} immediately."
                critical_shortage_count += 1

            radar_items.append({
                "category": cat_key.capitalize(),
                "unit": benchmark["unit"],
                "available_stock": round(available_stock, 1),
                "predicted_demand": round(required_demand, 1),
                "shortage_gap": round(gap, 1),
                "coverage_ratio": round(min(ratio, 9.99), 2),
                "status_code": status_code,
                "status_label": status_label,
                "urgency": urgency,
                "recommendation": recommendation,
            })

        overall_threat = "GREEN"
        if critical_shortage_count > 0:
            overall_threat = "RED"
        elif warning_shortage_count > 0:
            overall_threat = "ORANGE"

        return {
            "radar_timestamp": datetime.now(timezone.utc).isoformat(),
            "horizon_days": horizon_days,
            "affected_population_modeled": total_affected_pop,
            "overall_threat_level": overall_threat,
            "critical_shortage_items_count": critical_shortage_count,
            "warning_shortage_items_count": warning_shortage_count,
            "categories": radar_items,
        }


shortage_radar_service = ResourceShortageRadarService()
