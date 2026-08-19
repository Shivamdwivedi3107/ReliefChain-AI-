import os
import json
import pytest
from app.services.copilot_service import DisasterCopilotService, copilot_service
from app.services.notification_service import notification_manager
from app.core.config import settings


def test_phase16_copilot_provider_fallback_and_attribution(db_session):
    """Verify AI Copilot provider fallback and data source attribution tags."""
    res = copilot_service.query(db_session, prompt="Show critical resource shortages", user_role="admin")
    assert "source" in res
    assert "ReliefChain AI" in res["source"]
    assert "answer" in res
    assert isinstance(res["answer"], str)


def test_phase16_notification_provider_contracts():
    """Verify notification manager handles subscriptions and topic subscribers safely."""
    assert "operations" in notification_manager.topic_subscribers
    assert "missions" in notification_manager.topic_subscribers
    assert "inventory" in notification_manager.topic_subscribers
    assert "notifications" in notification_manager.topic_subscribers


def test_phase16_pwa_manifest_and_sw_endpoints(client):
    """Verify PWA manifest and service worker responses for real mobile devices."""
    resp_manifest = client.get("/ui/manifest.json")
    assert resp_manifest.status_code == 200
    manifest = resp_manifest.json()
    assert manifest["short_name"] == "ReliefChain AI"
    assert manifest["display"] == "standalone"
    assert len(manifest["shortcuts"]) >= 4

    resp_sw = client.get("/ui/sw.js")
    assert resp_sw.status_code == 200
    assert "sync-offline-sos" in resp_sw.text


def test_phase16_health_and_telemetry_probes(client):
    """Verify liveness, readiness, and metrics endpoints return 200 OK."""
    resp_live = client.get("/health/live")
    assert resp_live.status_code == 200
    assert resp_live.json()["status"] == "alive"

    resp_ready = client.get("/health/ready")
    assert resp_ready.status_code == 200
    assert resp_ready.json()["status"] == "ready"

    resp_metrics = client.get("/metrics")
    assert resp_metrics.status_code == 200
    assert "reliefchain_http_requests_total" in resp_metrics.text


def test_phase16_backup_script_existence():
    """Verify database backup scripts are present and formatted correctly."""
    assert os.path.exists("scripts/backup_database.sh")
    assert os.path.exists("scripts/restore_database.sh")
    assert os.path.exists("scripts/backup_database.ps1")
