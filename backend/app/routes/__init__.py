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
from app.routes.notifications import router as notifications_router, ws_router
from app.routes.missions import router as missions_router
from app.routes.audit_logs import router as audit_router
from app.routes.geo import router as geo_router
from app.routes.evidence import router as evidence_router
from app.routes.simulation import router as simulation_router
from app.routes.metrics import router as metrics_router
from app.routes.incidents import router as incidents_router
from app.routes.situation_reports import router as situation_reports_router
from app.routes.disaster_intelligence import router as disaster_intel_router
from app.routes.command_center import router as command_center_router
from app.routes.copilot import router as copilot_router
from app.routes.shortage_radar import router as shortage_radar_router
from app.routes.transparency import router as transparency_router
from app.routes.demo import router as demo_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(users_router)
api_router.include_router(orgs_router)
api_router.include_router(dashboards_router)
api_router.include_router(disasters_router)
api_router.include_router(relief_requests_router)
api_router.include_router(missions_router)
api_router.include_router(geo_router)
api_router.include_router(evidence_router)
api_router.include_router(simulation_router)
api_router.include_router(shortage_radar_router)
api_router.include_router(resources_router)
api_router.include_router(donations_router)
api_router.include_router(distributions_router)
api_router.include_router(blockchain_router)
api_router.include_router(qr_router)
api_router.include_router(ai_router)
api_router.include_router(analytics_router)
api_router.include_router(notifications_router)
api_router.include_router(audit_router)
api_router.include_router(incidents_router)
api_router.include_router(situation_reports_router)
api_router.include_router(disaster_intel_router)
api_router.include_router(command_center_router)
api_router.include_router(copilot_router)
api_router.include_router(transparency_router)
api_router.include_router(demo_router)


__all__ = ["api_router", "ws_router", "metrics_router"]


