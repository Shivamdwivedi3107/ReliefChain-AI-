from fastapi import APIRouter, status
from app.schemas.ai import AIPriorityPredictRequest, AIPriorityPredictResponse
from app.services.ai_service import calculate_priority_score_details, predict_emergency_priority

router = APIRouter(prefix="/ai", tags=["AI Emergency Decision Support"])


@router.post(
    "/predict-priority",
    response_model=AIPriorityPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict emergency request priority triage tier (Decision Support)",
)
def predict_priority(payload: AIPriorityPredictRequest):
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
        model_version="1.2.0-dss-rule-engine",
    )
