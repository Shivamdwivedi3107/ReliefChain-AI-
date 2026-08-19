from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_active_user, get_optional_user
from app.models.user import User
from app.services.copilot_service import copilot_service

router = APIRouter(prefix="/copilot", tags=["AI Disaster Copilot"])


class CopilotQueryRequest(BaseModel):
    prompt: str = Field(..., min_length=2, max_length=500, description="Natural command query or question")
    incident_id: Optional[str] = Field(None, description="Optional incident context ID")


@router.post("/query", summary="Query the AI Disaster Copilot")
def query_copilot(
    payload: CopilotQueryRequest,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_optional_user),
) -> Dict[str, Any]:
    """
    Query the AI Disaster Copilot for situational reasoning, incident diagnosis,
    resource shortages, and volunteer dispatch suggestions based on live data.
    """
    role = current_user.role if current_user else "admin"
    return copilot_service.query(
        db=db,
        prompt=payload.prompt,
        user_role=role,
        incident_id=payload.incident_id,
    )


@router.get("/suggested-prompts", summary="Get list of recommended copilot prompts")
def get_suggested_prompts() -> List[Dict[str, str]]:
    """Return pre-configured quick command prompts."""
    return copilot_service.SUGGESTED_PROMPTS
