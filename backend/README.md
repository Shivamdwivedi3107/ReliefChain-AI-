# ReliefChain AI — Backend Engine

FastAPI-powered high-throughput asynchronous engine for intelligent humanitarian aid coordination, real-time disaster intelligence, formal incident lifecycle state machines, multi-hazard external feed ingestion, multi-factor operational escalation modeling, situation reports (SITREPs), SPHERE-based resource forecasting, GIS hotspot clustering, and SHA-256 hash-linked transparency ledger.

## Architecture & Core Modules

- **FastAPI Core**: High-concurrency async RESTful API engine with automatic OpenAPI / Swagger and ReDoc documentation.
- **SQLAlchemy 2.0 ORM**: Dual-dialect persistence supporting SQLite for local zero-dependency testing and PostgreSQL 16 for production with connection pooling (`pool_pre_ping`, `pool_size`, `max_overflow`).
- **Role-Based Access Control (RBAC)**: Fine-grained security using standard JWT with HS256 algorithm enforcing access across Citizen, NGO, Field Volunteer, Donor, and Administrator roles.
- **Phase 9 Real-Time Disaster Intelligence & Incident Command**:
  - **Disaster Ingestion Provider Architecture** (`app/services/disaster_intelligence/`): Abstract base provider, mock radar provider, provider registry, normalization and deduplication engine (`POST /api/v1/disaster-intelligence/sync`, `GET /api/v1/disaster-intelligence/events`).
  - **Incident Lifecycle State Machine** (`app/services/incident_service.py`): Strict lifecycle transitions (`DETECTED -> VERIFIED -> ACTIVE -> MONITORING -> CONTAINED -> RESOLVED`) with automated immutable chronological audit timeline recording (`/api/v1/incidents`).
  - **Operational Escalation Engine** (`app/services/escalation_service.py`): Multi-factor threat modeling evaluating disaster severity, SOS density, medical emergencies, casualties, and displacement to compute 0–100 threat scores and escalation levels (`POST /api/v1/incidents/{id}/evaluate-escalation`).
  - **Situation Reports (SITREPs)** (`app/routes/situation_reports.py`): Structured field reporting for recon, triage, logistics, infrastructure, and containment.
  - **Command Center Summary** (`app/routes/command_center.py`): High-level operational readiness, active incidents, severity distributions, and activity telemetry (`GET /api/v1/command-center/summary`).
  - **Geospatial Impact Zone & GeoJSON Feed** (`app/services/geo_service.py`): Proximity queries and RFC 7946 map feeds (`GET /api/v1/geo/incidents/nearby`, `GET /api/v1/geo/map`).
- **Phase 8 Advanced AI Intelligence**:
  - Disaster risk prediction, SPHERE resource demand forecasting, 4-factor volunteer smart matching, impact simulation sandbox, and AI model registry.
- **Observability & OpenMetrics**: Thread-safe `AppMetricsCollector` exporting Prometheus text and JSON metrics on `GET /metrics`.
- **Security Hardening**: OWASP headers, correlation IDs, role-tiered sliding window rate limiting.
- **Tamper-Evident Ledger**: Sequential SHA-256 previous-hash blockchain linking across donations, allocations, deliveries, and simulations with whole-chain verification (`GET /api/v1/ledger/verify`).

## Quick Start

### 1. Environment Setup
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 2. Run Database Migrations / Local Engine
```powershell
py -3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. Run Automated Pytest Suite
```powershell
py -3 -m pytest
```
*Current test suite: **143 passed, 0 failed (100% pass rate)**.*

### 4. Interactive Endpoints
- **Operations Dashboard & Command Center**: `http://localhost:8000/ui/`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Telemetry Metrics**: `http://localhost:8000/metrics`
- **Health Probes**: `http://localhost:8000/health/ready` and `http://localhost:8000/health/live`

