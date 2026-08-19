from typing import Dict, Any, List
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user, get_optional_user
from app.models.user import User
from app.services.demo_scenario_service import demo_scenario_service

router = APIRouter(prefix="/demo", tags=["Demo Mode & Scenarios"])


class LoadScenarioRequest(BaseModel):
    scenario_key: str = Field(..., description="Scenario identifier e.g. flood_cyclone_crisis, seismic_emergency, wildfire_evacuation")


@router.get("/scenarios", summary="List available presentation demo scenarios")
def list_demo_scenarios() -> List[Dict[str, Any]]:
    """Returns catalog of realistic multi-hazard demo scenarios."""
    return demo_scenario_service.list_scenarios()


@router.post("/scenarios/load", summary="Load a demo scenario into active state")
def load_demo_scenario(
    payload: LoadScenarioRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    Loads a multi-hazard crisis scenario with realistic incidents, SOS requests,
    and situation reports for competition demos and presentations.
    """
    return demo_scenario_service.load_scenario(
        db=db,
        scenario_key=payload.scenario_key,
        actor_user=current_user,
    )
