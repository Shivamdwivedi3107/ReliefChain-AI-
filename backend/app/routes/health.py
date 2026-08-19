from fastapi import APIRouter, status
from app.database import check_db_connection
from app.core.config import settings

router = APIRouter(tags=["Health & Status"])


@router.get("/health", status_code=status.HTTP_200_OK)
def get_health_status():
    """System health check endpoint verifying database connectivity and environment status."""
    db_ok = check_db_connection()
    return {
        "status": "healthy" if db_ok else "degraded",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "database_connected": db_ok,
        "api_version": "v1",
    }
