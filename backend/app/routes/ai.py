import os
import hashlib
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.ai import (
    AIPriorityPredictRequest,
    AIPriorityPredictResponse,
    AIRiskPredictRequest,
    AIResourceForecastRequest,
    AIDisasterSimulationRequest,
    AIModelActivateRequest,
)
from app.services.ai_service import calculate_priority_score_details, predict_emergency_priority
from app.services.risk_prediction import risk_prediction_service
from app.services.resource_forecasting import resource_forecasting_service
from app.services.volunteer_matching import volunteer_matching_service
from app.services.disaster_simulation import disaster_simulation_service
from app.services.model_registry import model_registry
from app.dependencies import get_current_active_user, get_current_user_optional, require_roles
from app.models.user import User
from app.models.audit_log import AuditLog
from app.models.ai_models import (
    DisasterRiskPredictionRecord,
    ResourceForecastRecord,
    DisasterSimulationRecord,
)
from app.models.blockchain import BlockchainTransaction
from app.core.metrics import metrics_collector
from app.core.logging import logger

router = APIRouter(prefix="/ai", tags=["AI Emergency Decision Support, Risk & Forecasting"])


# -----------------------------------------------------------------------------
# 1. Existing Priority Triage & Explainability Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/predict-priority",
    response_model=AIPriorityPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict emergency request priority triage tier (Decision Support)",
)
def predict_priority(payload: AIPriorityPredictRequest):
    metrics_collector.record_ai_prediction()

    details = calculate_priority_score_details(
        disaster_type=payload.disaster_type,
        affected_people=payload.affected_people,
        location_risk_score=payload.location_risk_score,
        food_needed=payload.food_needed,
        water_needed=payload.water_needed,
        medical_needed=payload.medical_needed,
        vulnerable_population=payload.vulnerable_population,
        time_elapsed_hours=payload.time_elapsed_hours,
        request_id=payload.request_id,
    )

    _, confidence, factors = predict_emergency_priority(
        disaster_type=payload.disaster_type,
        affected_people=payload.affected_people,
        location_risk_score=payload.location_risk_score,
        food_needed=payload.food_needed,
        water_needed=payload.water_needed,
        medical_needed=payload.medical_needed,
        vulnerable_population=payload.vulnerable_population,
        time_elapsed_hours=payload.time_elapsed_hours,
    )

    return AIPriorityPredictResponse(
        request_id=payload.request_id,
        priority_score=details["priority_score"],
        priority_level=details["priority_level"],
        predicted_priority=details["priority_slug"],
        confidence_score=confidence,
        explanation=details["explanation"],
        contributing_factors=factors,
        model_version="2.4.0-rf-dss",
    )


@router.post(
    "/explain-priority",
    summary="Detailed Explainable AI (XAI) breakdown of emergency priority score",
)
def explain_priority(payload: AIPriorityPredictRequest):
    metrics_collector.record_ai_prediction()

    details = calculate_priority_score_details(
        disaster_type=payload.disaster_type,
        affected_people=payload.affected_people,
        location_risk_score=payload.location_risk_score,
        food_needed=payload.food_needed,
        water_needed=payload.water_needed,
        medical_needed=payload.medical_needed,
        vulnerable_population=payload.vulnerable_population,
        time_elapsed_hours=payload.time_elapsed_hours,
        request_id=payload.request_id,
    )

    pred_slug, confidence, _ = predict_emergency_priority(
        disaster_type=payload.disaster_type,
        affected_people=payload.affected_people,
        location_risk_score=payload.location_risk_score,
        food_needed=payload.food_needed,
        water_needed=payload.water_needed,
        medical_needed=payload.medical_needed,
        vulnerable_population=payload.vulnerable_population,
        time_elapsed_hours=payload.time_elapsed_hours,
    )

    factors: List[Dict[str, Any]] = []
    if payload.medical_needed:
        factors.append({
            "name": "medical_trauma",
            "contribution": 30,
            "reason": "Immediate medical attention or surgical trauma support required",
        })
    if payload.vulnerable_population:
        factors.append({
            "name": "vulnerable_population",
            "contribution": 20,
            "reason": "Infants, elderly, or mobility-impaired individuals stranded in disaster area",
        })
    if payload.affected_people > 20:
        factors.append({
            "name": "high_casualty_density",
            "contribution": 20,
            "reason": f"Large affected group ({payload.affected_people} individuals reported)",
        })
    elif payload.affected_people > 5:
        factors.append({
            "name": "moderate_casualty_density",
            "contribution": 10,
            "reason": f"Cluster of {payload.affected_people} affected individuals",
        })
    if payload.location_risk_score > 0.7:
        factors.append({
            "name": "high_location_hazard",
            "contribution": 15,
            "reason": f"Severe location hazard index ({payload.location_risk_score:.2f})",
        })
    if payload.food_needed or payload.water_needed:
        factors.append({
            "name": "subsistence_deprivation",
            "contribution": 10,
            "reason": "Critical potable water and nutrition exhaustion",
        })

    return {
        "success": True,
        "request_id": payload.request_id,
        "priority_score": details["priority_score"],
        "priority_level": details["priority_level"],
        "predicted_tier": pred_slug.upper(),
        "model_confidence": confidence,
        "explanation": details["explanation"],
        "factors": factors,
        "dss_disclaimer": "This analysis is produced by the ReliefChain Decision Support System. Responders should verify situational conditions.",
    }


# -----------------------------------------------------------------------------
# 2. Phase 8: Disaster Risk Prediction Endpoint
# -----------------------------------------------------------------------------

@router.post(
    "/risk-predict",
    summary="Predict multi-factor disaster vulnerability risk score (Hybrid AI DSS)",
    status_code=status.HTTP_200_OK,
)
def predict_disaster_risk(
    payload: AIRiskPredictRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    metrics_collector.record_ai_prediction()

    result = risk_prediction_service.predict_risk(
        disaster_type=payload.disaster_type,
        historical_severity=payload.historical_severity,
        rainfall_mm=payload.rainfall_mm,
        temperature_c=payload.temperature_c,
        population_density=payload.population_density,
        vulnerable_population_pct=payload.vulnerable_population_pct,
        infrastructure_risk_score=payload.infrastructure_risk_score,
        previous_disaster_frequency=payload.previous_disaster_frequency,
        resource_availability_score=payload.resource_availability_score,
        location_name=payload.location_name or "Target Disaster Zone",
        latitude=payload.latitude,
        longitude=payload.longitude,
    )

    # Persist risk assessment record to database
    try:
        record = DisasterRiskPredictionRecord(
            disaster_type=payload.disaster_type,
            location_name=payload.location_name or "Target Zone",
            latitude=payload.latitude,
            longitude=payload.longitude,
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            confidence=result["confidence"],
            input_parameters=payload.model_dump(),
            risk_factors=result["risk_factors"],
            recommendations=result["recommendations"],
            model_version=result["model_version"],
            created_by_user_id=current_user.id if current_user else None,
        )
        db.add(record)

        # Audit log entry for critical hazard predictions
        if result["risk_level"] in ("CRITICAL", "HIGH"):
            audit = AuditLog(
                user_id=current_user.id if current_user else None,
                action="DISASTER_RISK_PREDICTED",
                entity_type="disaster_risk",
                entity_id=record.id,
                details_json={
                    "disaster_type": payload.disaster_type,
                    "risk_score": result["risk_score"],
                    "risk_level": result["risk_level"],
                },
            )
            db.add(audit)
        db.commit()
        result["prediction_id"] = record.id
    except Exception as exc:
        db.rollback()
        logger.warning(f"[RiskPrediction] DB record save note: {exc}")

    return result


# -----------------------------------------------------------------------------
# 3. Phase 8: Resource Demand Forecasting Endpoint
# -----------------------------------------------------------------------------

@router.post(
    "/resource-forecast",
    summary="Forecast future supply demand burn rates and warehouse inventory gaps",
    status_code=status.HTTP_200_OK,
)
def forecast_resource_demand(
    payload: AIResourceForecastRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "ngo"])),
):
    metrics_collector.record_ai_prediction()

    result = resource_forecasting_service.forecast_demand_and_gaps(
        disaster_type=payload.disaster_type,
        severity=payload.severity,
        population_affected=payload.population_affected,
        active_sos_requests=payload.active_sos_requests,
        disaster_duration_hours=payload.disaster_duration_hours,
        forecast_period_hours=payload.forecast_period_hours,
        organization_id=payload.organization_id or current_user.organization_id,
        db_session=db,
    )

    # Persist forecast record
    try:
        forecast_record = ResourceForecastRecord(
            disaster_type=payload.disaster_type,
            severity=payload.severity,
            population_affected=payload.population_affected,
            forecast_period_hours=payload.forecast_period_hours,
            predicted_demand=result["predicted_demand"],
            inventory_gap=result["inventory_gap"],
            recommendations=result["recommendations"],
            organization_id=payload.organization_id or current_user.organization_id,
            created_by_user_id=current_user.id,
        )
        db.add(forecast_record)

        # Audit log entry
        audit = AuditLog(
            user_id=current_user.id,
            action="RESOURCE_DEMAND_FORECAST_GENERATED",
            entity_type="resource_forecast",
            entity_id=forecast_record.id,
            details_json={
                "disaster_type": payload.disaster_type,
                "has_shortage": result["has_shortage"],
                "gaps": result["inventory_gap"],
            },
        )
        db.add(audit)
        db.commit()
        result["forecast_id"] = forecast_record.id
    except Exception as exc:
        db.rollback()
        logger.warning(f"[ResourceForecast] DB save note: {exc}")

    return result


# -----------------------------------------------------------------------------
# 4. Phase 8: Volunteer Intelligent Assignment Recommendations
# -----------------------------------------------------------------------------

@router.get(
    "/volunteer-recommendations/{mission_id}",
    summary="Retrieve ranked volunteer matching recommendations for a relief mission",
    status_code=status.HTTP_200_OK,
)
def get_volunteer_recommendations(
    mission_id: str,
    limit: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin", "ngo"])),
):
    metrics_collector.record_ai_prediction()

    result = volunteer_matching_service.get_recommendations_for_mission(
        db=db,
        mission_id=mission_id,
        limit=limit,
    )
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", f"Mission '{mission_id}' not found."),
        )
    return result


# -----------------------------------------------------------------------------
# 5. Phase 8: Disaster Impact Simulation Lab (Admin Only)
# -----------------------------------------------------------------------------

@router.post(
    "/simulate-disaster",
    summary="Admin-only: Run contingency disaster impact scenario simulation",
    status_code=status.HTTP_200_OK,
)
def simulate_disaster_scenario(
    payload: AIDisasterSimulationRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    metrics_collector.record_ai_prediction()

    result = disaster_simulation_service.run_simulation(
        scenario_title=payload.scenario_title,
        disaster_type=payload.disaster_type,
        severity=payload.severity,
        population_affected=payload.population_affected,
        duration_hours=payload.duration_hours,
        location_name=payload.location_name,
    )

    # Persist simulation record
    try:
        sim_record = DisasterSimulationRecord(
            scenario_title=payload.scenario_title,
            disaster_type=payload.disaster_type,
            severity=payload.severity,
            population_affected=payload.population_affected,
            duration_hours=payload.duration_hours,
            location_name=payload.location_name,
            simulation_results=result,
            created_by_user_id=current_user.id,
        )
        db.add(sim_record)
        db.flush()

        # Audit log
        audit = AuditLog(
            user_id=current_user.id,
            action="DISASTER_SIMULATION_EXECUTED",
            entity_type="disaster_simulation",
            entity_id=sim_record.id,
            details_json={
                "scenario_title": payload.scenario_title,
                "disaster_type": payload.disaster_type,
                "severity": payload.severity,
            },
        )
        db.add(audit)

        # Seal simulation event in SHA-256 Ledger
        sim_payload_bytes = f"{sim_record.id}:{payload.scenario_title}:{payload.severity}:{payload.population_affected}".encode()
        record_hash = hashlib.sha256(sim_payload_bytes).hexdigest()
        
        last_tx = db.query(BlockchainTransaction).order_by(BlockchainTransaction.created_at.desc()).first()
        prev_hash = last_tx.record_hash if last_tx else "0" * 64

        ledger_tx = BlockchainTransaction(
            event_type="disaster_simulation",
            reference_id=sim_record.id,
            record_hash=record_hash,
            previous_hash=prev_hash,
            status="confirmed",
        )
        db.add(ledger_tx)
        db.commit()
        result["simulation_id"] = sim_record.id
        result["ledger_tx_id"] = ledger_tx.id
    except Exception as exc:
        db.rollback()
        logger.warning(f"[DisasterSimulation] DB save note: {exc}")

    return result


# -----------------------------------------------------------------------------
# 6. Phase 8: AI Model Catalog, Inspection & Activation Endpoints
# -----------------------------------------------------------------------------

@router.get(
    "/models",
    summary="List all registered AI/ML models in the governance catalog",
    status_code=status.HTTP_200_OK,
)
def list_ai_models(
    current_user: User = Depends(get_current_active_user),
):
    return {
        "success": True,
        "models": model_registry.list_models(),
    }


@router.get(
    "/models/{model_name}",
    summary="Retrieve detailed model card, performance metrics, and governance parameters",
    status_code=status.HTTP_200_OK,
)
def get_ai_model_details(
    model_name: str,
    current_user: User = Depends(get_current_active_user),
):
    model_card = model_registry.get_model(model_name)
    if not model_card:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"AI model '{model_name}' not found in registry.",
        )
    return {
        "success": True,
        "model": model_card,
    }


@router.post(
    "/models/activate",
    summary="Admin-only: Activate or deactivate a registered AI model",
    status_code=status.HTTP_200_OK,
)
def activate_ai_model(
    payload: AIModelActivateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(["admin"])),
):
    result = model_registry.activate_model(payload.model_name, payload.is_active)
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=result.get("error", "Model activation failed."),
        )

    # Audit log
    audit = AuditLog(
        user_id=current_user.id,
        action="AI_MODEL_ACTIVATION_TOGGLED",
        entity_type="ai_model",
        entity_id=payload.model_name,
        details_json={"model_name": payload.model_name, "is_active": payload.is_active},
    )
    db.add(audit)
    db.commit()

    return result


@router.get(
    "/model-info",
    summary="Retrieve primary Random Forest Model Metadata, Performance Metrics, and Feature Weights",
)
def get_model_info():
    """Retrieve metadata, performance metrics, and SHA-256 checksum from model registry."""
    return model_registry.get_model_info()


@router.post(
    "/reload-model",
    summary="Admin-only: Hot-reload and verify machine learning model artifact from disk",
)
def reload_model(
    current_user: User = Depends(require_roles(["admin"])),
):
    """
    Safely reloads the AI model from disk, recalculates the SHA-256 checksum,
    and returns status without dropping service availability.
    """
    result = model_registry.reload_model()
    return result
