from typing import Optional
from fastapi import APIRouter, Depends, Query, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.simulation_service import simulation_engine

router = APIRouter(prefix="/simulation", tags=["Disaster Simulation Operations"])


@router.post("/start", summary="Start disaster drill simulation and inject realistic synthetic emergency scenarios")
def start_simulation(
    scenario: str = Body(default="cyclone_landing", embed=True),
    db: Session = Depends(get_db),
):
    result = simulation_engine.start_simulation(db=db, scenario_key=scenario)
    return {"success": True, "simulation": result}


@router.post("/stop", summary="Stop active disaster simulation and purge synthetic records")
def stop_simulation(
    purge_data: bool = Body(default=True, embed=True),
    db: Session = Depends(get_db),
):
    result = simulation_engine.stop_simulation(db=db, purge_simulated_data=purge_data)
    return {"success": True, "simulation": result}


@router.get("/status", summary="Get live simulation mode status and active drill metrics")
def get_simulation_status():
    status = simulation_engine.get_status()
    return {"success": True, "simulation": status}
