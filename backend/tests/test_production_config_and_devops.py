import os
import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from app.core.config import Settings
from app.core.logging import request_id_ctx_var
from app.core.rate_limit import InMemoryRateLimiter
from app.main import app


def test_production_settings_rejects_insecure_secret():
    """Verify that Settings raises a validation error if deployed in production with default/short secret."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="reliefchain-dev-super-secret-key-change-in-production-12345",
        )
    assert "CRITICAL SECURITY CONFIGURATION ERROR" in str(excinfo.value)


def test_production_settings_rejects_short_secret():
    """Verify that Settings rejects secrets under 32 characters in production mode."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="short-secret",
        )
    assert "at least 32 characters" in str(excinfo.value)


def test_production_settings_rejects_wildcard_cors():
    """Verify that Settings rejects wildcard CORS origins in production mode."""
    with pytest.raises(ValidationError) as excinfo:
        Settings(
            ENVIRONMENT="production",
            DEBUG=False,
            SECRET_KEY="valid-cryptographically-secure-key-32-chars-long!",
            BACKEND_CORS_ORIGINS=["*"],
        )
    assert "CORS cannot allow wildcard" in str(excinfo.value)


def test_database_url_normalization():
    """Verify postgres:// is safely converted to postgresql+psycopg2:// dialect."""
    s = Settings(
        ENVIRONMENT="development",
        DATABASE_URL="postgres://user:pass@localhost:5432/reliefchain",
    )
    assert s.DATABASE_URL.startswith("postgresql+psycopg2://")


def test_cors_origins_string_comma_separated_parsing():
    """Verify string comma-separated CORS configuration parsing."""
    s = Settings(
        ENVIRONMENT="development",
        BACKEND_CORS_ORIGINS="http://localhost:3000,http://app.reliefchain.org",
    )
    assert "http://localhost:3000" in s.BACKEND_CORS_ORIGINS
    assert "http://app.reliefchain.org" in s.BACKEND_CORS_ORIGINS


def test_request_id_middleware_header(client: TestClient):
    """Verify that every HTTP response includes X-Request-ID and X-Process-Time-Ms."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "x-request-id" in response.headers
    assert "x-process-time-ms" in response.headers
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"


def test_custom_request_id_propagation(client: TestClient):
    """Verify incoming X-Request-ID is preserved and echoed back."""
    custom_id = "test-req-correlation-998877"
    response = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response.status_code == 200
    assert response.headers["x-request-id"] == custom_id


def test_in_memory_rate_limiter_logic():
    """Verify sliding window rate limiter behavior directly."""
    from app.core.config import settings
    orig_state = settings.RATE_LIMIT_ENABLED
    settings.RATE_LIMIT_ENABLED = True
    try:
        limiter = InMemoryRateLimiter()
        key = "test_user_ip:endpoint"

        # Allow up to 3 requests in 60s
        allowed_1, _ = limiter.is_allowed(key, max_requests=3, window_seconds=60)
        allowed_2, _ = limiter.is_allowed(key, max_requests=3, window_seconds=60)
        allowed_3, _ = limiter.is_allowed(key, max_requests=3, window_seconds=60)
        allowed_4, retry_after = limiter.is_allowed(key, max_requests=3, window_seconds=60)

        assert allowed_1 is True
        assert allowed_2 is True
        assert allowed_3 is True
        assert allowed_4 is False
        assert retry_after > 0
    finally:
        settings.RATE_LIMIT_ENABLED = orig_state


def test_health_probes_full_readiness(client: TestClient):
    """Verify /health/ready returns status ok and database connected."""
    response = client.get("/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("ok", "ready")
    assert data["database"] in ("connected", "ok", True)


def test_docker_and_ci_configuration_files_exist():
    """Verify deployment configuration files exist in the repository."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    
    dockerfile_path = os.path.join(root_dir, "Dockerfile")
    docker_compose_path = os.path.join(root_dir, "docker-compose.yml")
    ci_workflow_path = os.path.join(root_dir, ".github", "workflows", "ci.yml")
    pyproject_path = os.path.join(root_dir, "pyproject.toml")
    dockerignore_path = os.path.join(root_dir, ".dockerignore")

    assert os.path.isfile(dockerfile_path), "Dockerfile must exist"
    assert os.path.isfile(docker_compose_path), "docker-compose.yml must exist"
    assert os.path.isfile(ci_workflow_path), "ci.yml must exist"
    assert os.path.isfile(pyproject_path), "pyproject.toml must exist"
    assert os.path.isfile(dockerignore_path), ".dockerignore must exist"
