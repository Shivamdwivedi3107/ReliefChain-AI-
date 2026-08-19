from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.relief_request import ReliefRequest
from app.models.qr_verification import QRVerification
from app.models.donation import Donation
from app.models.notification import Notification
from app.services.metrics_service import metrics_collector
from app.services.notification_service import notification_manager

router = APIRouter(tags=["Monitoring & Telemetry Metrics"])


@router.get("/metrics", summary="Prometheus and OpenMetrics telemetry endpoint")
def get_metrics(request: Request, db: Session = Depends(get_db)):
    # Gather live database entity counts
    db_stats = {
        "relief_requests": db.query(ReliefRequest).count(),
        "completed_missions": db.query(ReliefRequest).filter(ReliefRequest.status == "completed").count(),
        "qr_verifications": db.query(QRVerification).filter(QRVerification.status == "verified").count(),
        "donations": db.query(Donation).count(),
        "notifications": db.query(Notification).count(),
    }
    active_ws = notification_manager.total_active_connections

    # Check accept header: if application/json requested, return JSON, else return standard Prometheus text/plain
    accept = request.headers.get("accept", "")
    if "application/json" in accept:
        return metrics_collector.get_metrics_summary(db_stats=db_stats, active_ws_count=active_ws)

    prom_text = metrics_collector.generate_prometheus_text(db_stats=db_stats, active_ws_count=active_ws)
    return Response(content=prom_text, media_type="text/plain; version=0.0.4")
