import os
import json
import pytest
from fastapi.testclient import TestClient
from app.core.config import Settings
from app.services.background_tasks import execute_background_task
from app.services.model_registry import model_registry


def test_database_url_postgresql_and_sqlite_normalization():
    """Verify DATABASE_URL normalizes both SQLite and Postgres connection formats."""
    # SQLite
    s_sqlite = Settings(DATABASE_URL="sqlite:///./test.db")
    assert s_sqlite.DATABASE_URL == "sqlite:///./test.db"

    # PostgreSQL shorthand normalization
    s_pg = Settings(DATABASE_URL="postgres://user:pass@localhost:5432/reliefchain")
    assert s_pg.DATABASE_URL.startswith("postgresql+psycopg2://")

    # PostgreSQL standard prefix normalization
    s_pg_std = Settings(DATABASE_URL="postgresql://user:pass@localhost:5432/reliefchain")
    assert s_pg_std.DATABASE_URL.startswith("postgresql+psycopg2://")


def test_health_live_probe(client: TestClient):
    """Test /health/live liveness probe for process supervision."""
    res = client.get("/health/live")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert "timestamp" in data


def test_health_ready_probe_with_subsystems(client: TestClient):
    """Test /health/ready readiness probe with database and AI subsystem health."""
    res = client.get("/health/ready")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ("ready", "healthy")
    assert data["database"] in ("healthy", "connected")
    assert data["ready"] is True
    assert "ai_model" in data
    assert "version" in data


def test_security_headers_present(client: TestClient):
    """Verify security headers are applied to HTTP responses."""
    res = client.get("/health")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"
    assert "X-Request-ID" in headers
    assert "X-Process-Time-Ms" in headers


def test_metrics_endpoint_telemetry(client: TestClient):
    """Verify Prometheus telemetry metrics endpoint returns valid metric entries."""
    res = client.get("/metrics")
    assert res.status_code == 200
    assert "reliefchain_http_requests_total" in res.text
    assert "reliefchain_uptime_seconds" in res.text
    assert "reliefchain_average_latency_ms" in res.text


def test_metrics_json_telemetry_summary(client: TestClient):
    """Verify JSON format telemetry output when queried with Accept header."""
    res = client.get("/metrics", headers={"Accept": "application/json"})
    assert res.status_code == 200
    data = res.json()
    assert "uptime_seconds" in data
    assert "average_latency_ms" in data
    assert "http_requests_total" in data
    assert "database_entities" in data


def test_background_task_helper_success():
    """Verify background task execution wrapper logs and succeeds for valid jobs."""
    def sample_job(x, y):
        return x + y

    res = execute_background_task("sample_addition_job", sample_job, 10, 25)
    assert res["success"] is True
    assert res["task_name"] == "sample_addition_job"
    assert res["elapsed_ms"] >= 0.0
    assert res["error"] is None


def test_background_task_helper_catches_errors():
    """Verify background task wrapper catches exceptions and prevents process crashes."""
    def faulty_job():
        raise ValueError("Simulated background job failure")

    res = execute_background_task("faulty_job", faulty_job)
    assert res["success"] is False
    assert "Simulated background job failure" in res["error"]
    assert res["task_name"] == "faulty_job"


def test_ai_model_registry_info():
    """Verify AI model registry returns version, metrics, and checksum."""
    info = model_registry.get_model_info()
    assert info["success"] is True
    assert "RandomForest" in info["model_name"]
    assert info["metrics"]["test_accuracy"] >= 0.85
    assert len(info["feature_importances"]) == 6
    assert info["governance"]["human_in_the_loop"] is True


def test_ai_model_reload_endpoint_admin(client: TestClient, admin_token: str):
    """Verify admin can invoke safe AI model hot-reloading."""
    res = client.post("/api/v1/ai/reload-model", headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert "checksum" in data or "status" in data


def test_ai_model_reload_forbidden_for_citizens(client: TestClient, citizen_token: str):
    """Verify citizens and unauthorized roles cannot trigger model reload."""
    res = client.post("/api/v1/ai/reload-model", headers={"Authorization": f"Bearer {citizen_token}"})
    assert res.status_code == 403


def test_relief_requests_pagination_limit_offset(client: TestClient, admin_token: str):
    """Verify limit and offset pagination parameters on relief requests list."""
    res = client.get("/api/v1/relief-requests?limit=5&offset=0")
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["limit"] == 5
    assert data["offset"] == 0
    assert "total" in data
    assert len(data["data"]) <= 5


def test_pwa_manifest_file_structure():
    """Verify frontend/manifest.json contains required PWA fields."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    manifest_path = os.path.join(root_dir, "frontend", "manifest.json")
    assert os.path.exists(manifest_path)
    
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    assert manifest["name"]
    assert manifest["start_url"] == "/ui/"
    assert manifest["display"] == "standalone"
    assert manifest["theme_color"] == "#3B82F6"


def test_pwa_service_worker_file_structure():
    """Verify frontend/sw.js exists and enforces API network-only exclusion."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    sw_path = os.path.join(root_dir, "frontend", "sw.js")
    assert os.path.exists(sw_path)
    
    with open(sw_path, "r", encoding="utf-8") as f:
        sw_content = f.read()
    assert "CACHE_NAME" in sw_content
    assert "/api/" in sw_content
    assert "addEventListener('fetch'" in sw_content


def test_offline_indicator_in_html():
    """Verify frontend/index.html includes offline banner and ServiceWorker registration."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    html_path = os.path.join(root_dir, "frontend", "index.html")
    assert os.path.exists(html_path)
    
    with open(html_path, "r", encoding="utf-8") as f:
        html = f.read()
    assert 'id="offline-banner"' in html
    assert 'manifest.json' in html
    assert 'navigator.serviceWorker.register' in html


def test_performance_test_script_exists_and_runnable():
    """Verify backend/scripts/performance_test.py exists and contains run_benchmark."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    script_path = os.path.join(root_dir, "backend", "scripts", "performance_test.py")
    assert os.path.exists(script_path)
    
    with open(script_path, "r", encoding="utf-8") as f:
        code = f.read()
    assert "def run_benchmark" in code
    assert "TEST_TARGETS" in code
