import os
import json
import logging
import hashlib
import tempfile
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings, settings
from app.core.logging import JsonLogFormatter, SensitiveDataFilter
from app.core.metrics import metrics_collector
from scripts.backup_db import run_backup, compute_sha256
from scripts.restore_db import verify_checksum


def test_environment_settings_development_defaults():
    """Verify default development configuration."""
    s = Settings(ENVIRONMENT="development")
    assert s.ENVIRONMENT == "development"
    assert s.API_V1_STR == "/api/v1"
    assert s.ALGORITHM == "HS256"


def test_environment_settings_staging_support():
    """Verify staging environment configuration is accepted."""
    s = Settings(
        ENVIRONMENT="staging",
        DEBUG=False,
        SECRET_KEY="staging-valid-cryptographic-key-32-chars-long-abc",
        BACKEND_CORS_ORIGINS=["https://staging.reliefchain.org"],
    )
    assert s.ENVIRONMENT == "staging"
    assert s.DEBUG is False


def test_production_settings_rejects_debug_true():
    """Verify production environment strictly rejects DEBUG=True."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            DEBUG=True,
            SECRET_KEY="production-valid-key-32-characters-long-12345",
            BACKEND_CORS_ORIGINS=["https://reliefchain.org"],
        )
    assert "DEBUG must be False in production" in str(exc.value)


def test_production_settings_rejects_weak_secret():
    """Verify production environment strictly rejects short or default secrets."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="short-insecure-key",
            BACKEND_CORS_ORIGINS=["https://reliefchain.org"],
        )
    assert "SECRET_KEY must be a cryptographically strong" in str(exc.value)


def test_production_settings_rejects_wildcard_cors():
    """Verify production environment rejects wildcard '*' CORS origin."""
    with pytest.raises(ValidationError) as exc:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="production-valid-key-32-characters-long-12345",
            BACKEND_CORS_ORIGINS=["*"],
        )
    assert "CORS cannot allow wildcard '*'" in str(exc.value)


def test_allowed_hosts_string_and_list_parsing():
    """Verify ALLOWED_HOSTS parses comma-separated string into list."""
    s = Settings(
        ALLOWED_HOSTS="api.reliefchain.org, localhost, 127.0.0.1",
        ENVIRONMENT="development",
    )
    assert s.ALLOWED_HOSTS == ["api.reliefchain.org", "localhost", "127.0.0.1"]


def test_database_url_postgresql_dialect_normalization():
    """Verify database URL normalizes legacy postgres:// to postgresql+psycopg2://."""
    url = "postgres://user:pass@dbhost:5432/reliefchain"
    normalized = Settings.normalize_database_url(url)
    assert normalized.startswith("postgresql+psycopg2://")


def test_structured_json_logging_output():
    """Verify JsonLogFormatter emits valid structured JSON records."""
    formatter = JsonLogFormatter()
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test_file.py",
        lineno=42,
        msg="Mission dispatched successfully to Zone B",
        args=(),
        exc_info=None,
    )
    record.request_id = "req-test-uuid-999"
    formatted = formatter.format(record)
    
    parsed = json.loads(formatted)
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "test_logger"
    assert parsed["message"] == "Mission dispatched successfully to Zone B"
    assert parsed["request_id"] == "req-test-uuid-999"


def test_sensitive_data_logging_masking():
    """Verify SensitiveDataFilter masks secrets, passwords, and bearer tokens."""
    filter_obj = SensitiveDataFilter()
    
    # Test password masking
    record1 = logging.LogRecord("test", logging.INFO, "test.py", 10, "Attempted login with password: 'SuperSecretPassword123'", (), None)
    filter_obj.filter(record1)
    assert "SuperSecretPassword123" not in record1.msg
    assert "***MASKED***" in record1.msg

    # Test token masking
    record2 = logging.LogRecord("test", logging.INFO, "test.py", 11, "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", (), None)
    filter_obj.filter(record2)
    assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in record2.msg


def test_alembic_ini_and_migration_files_present():
    """Verify Alembic configuration and migration versions exist."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    alembic_ini = base_dir / "backend" / "alembic.ini"
    env_py = base_dir / "backend" / "alembic" / "env.py"
    versions_dir = base_dir / "backend" / "alembic" / "versions"

    assert alembic_ini.exists(), "alembic.ini missing"
    assert env_py.exists(), "alembic/env.py missing"
    assert versions_dir.exists(), "alembic/versions directory missing"
    assert len(list(versions_dir.glob("*.py"))) >= 1, "No migration scripts found in alembic/versions"


def test_dockerfile_configuration_directives():
    """Verify production Dockerfile directives."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    dockerfile = base_dir / "Dockerfile"
    assert dockerfile.exists(), "Dockerfile missing"
    
    content = dockerfile.read_text(encoding="utf-8")
    assert "FROM python:" in content
    assert "reliefchain" in content  # Non-root user
    assert "HEALTHCHECK" in content
    assert "uvicorn" in content


def test_docker_compose_production_services_and_volumes():
    """Verify production Docker Compose file structure."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    compose_prod = base_dir / "docker-compose.prod.yml"
    assert compose_prod.exists(), "docker-compose.prod.yml missing"

    content = compose_prod.read_text(encoding="utf-8")
    assert "proxy:" in content
    assert "backend:" in content
    assert "db:" in content
    assert "postgres_data:" in content


def test_nginx_reverse_proxy_config_syntax_and_headers():
    """Verify Nginx reverse proxy configuration files exist and include key paths."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    nginx_conf = base_dir / "nginx" / "nginx.conf"
    default_conf = base_dir / "nginx" / "conf.d" / "default.conf"

    assert nginx_conf.exists(), "nginx/nginx.conf missing"
    assert default_conf.exists(), "nginx/conf.d/default.conf missing"

    content = default_conf.read_text(encoding="utf-8")
    assert "proxy_pass http://fastapi_backend;" in content
    assert "location /api/" in content
    assert "location /ws/" in content
    assert "X-Frame-Options" in content


def test_backup_script_execution_and_sha256_checksum(tmp_path):
    """Verify automated database backup creates archive and valid SHA-256 checksum."""
    res = run_backup(output_dir=str(tmp_path), retention_days=1)
    assert res["success"] is True
    assert Path(res["backup_file"]).exists()
    assert Path(res["checksum_file"]).exists()
    assert len(res["sha256"]) == 64

    # Verify checksum content matches
    calculated_hash = compute_sha256(Path(res["backup_file"]))
    assert calculated_hash == res["sha256"]


def test_restore_script_checksum_validation(tmp_path):
    """Verify restore utility catches checksum mismatches."""
    test_file = tmp_path / "test_snapshot.db"
    test_file.write_bytes(b"SQLite format 3\x00test-data")
    
    # Write valid checksum
    checksum = hashlib.sha256(test_file.read_bytes()).hexdigest()
    checksum_file = test_file.with_suffix(".db.sha256")
    checksum_file.write_text(f"{checksum}  {test_file.name}")

    assert verify_checksum(test_file) is True

    # Tamper with file
    test_file.write_bytes(b"Tampered data!")
    with pytest.raises(ValueError) as exc:
        verify_checksum(test_file)
    assert "Integrity Check Failure" in str(exc.value)


def test_health_probes_liveness_and_readiness_contracts(client: TestClient):
    """Verify contract response format of /health, /health/live, and /health/ready."""
    live_res = client.get("/health/live")
    assert live_res.status_code == 200
    assert live_res.json()["status"] == "alive"

    ready_res = client.get("/health/ready")
    assert ready_res.status_code == 200
    ready_data = ready_res.json()
    assert ready_data["status"] == "ready"
    assert "database" in ready_data
    assert "ai_model" in ready_data
    assert "ledger" in ready_data


def test_metrics_openmetrics_telemetry_fields(client: TestClient):
    """Verify Prometheus / OpenMetrics endpoint exports safe operational counters."""
    res = client.get("/metrics")
    assert res.status_code == 200
    content = res.text
    assert "reliefchain_uptime_seconds" in content
    assert "reliefchain_http_requests_total" in content
    assert "reliefchain_http_errors_total" in content


def test_frontend_runtime_config_file():
    """Verify frontend/js/config.js contains dynamic API and WS configuration."""
    base_dir = Path(__file__).resolve().parent.parent.parent
    config_js = base_dir / "frontend" / "js" / "config.js"
    assert config_js.exists(), "frontend/js/config.js missing"

    content = config_js.read_text(encoding="utf-8")
    assert "RELIEFCHAIN_CONFIG" in content
    assert "API_BASE" in content
    assert "WS_BASE" in content
    assert "2.0.0-phase7" in content
