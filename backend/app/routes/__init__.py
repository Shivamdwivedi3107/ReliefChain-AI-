from fastapi import APIRouter
from app.routes.health import router as health_router
from app.routes.auth import router as auth_router
from app.routes.users import router as users_router
from app.routes.organizations import router as orgs_router
from app.routes.dashboards import router as dashboards_router
from app.routes.disasters import router as disasters_router
from app.routes.relief_requests import router as relief_requests_router
from app.routes.resources import router as resources_router
from app.routes.donations import router as donations_router
from app.routes.distributions import router as distributions_router
from app.routes.blockchain import router as blockchain_router
from app.routes.qr import router as qr_router
from app.routes.ai import router as ai_router
from app.routes.analytics import router as analytics_router
from app.routes.notifications import router as notifications_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(orgs_router)
api_router.include_router(dashboards_router)
api_router.include_router(disasters_router)
api_router.include_router(relief_requests_router)
api_router.include_router(resources_router)
api_router.include_router(donations_router)
api_router.include_router(distributions_router)
api_router.include_router(blockchain_router)
api_router.include_router(qr_router)
api_router.include_router(ai_router)
api_router.include_router(analytics_router)
api_router.include_router(notifications_router)

__all__ = ["api_router"]
