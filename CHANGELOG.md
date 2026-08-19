# Changelog — ReliefChain AI

All notable changes to the **ReliefChain AI** platform are documented in this file.
The project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [v1.0.0] - 2026-08-20 — Phase 15 Real-World Launch & Production Release

### Phase 15: Real-World Launch & Production Deployment
- **Human-in-the-Loop Safety**: Added explicit emergency authority disclaimers to Citizen SOS modal and AI Copilot consoles, affirming human decision-making authority for life-safety actions.
- **Warning Isolation**: Added `pytest.ini` filterwarnings for third-party `joblib.numpy_pickle` unpickling deprecation notices under NumPy 2.5, delivering zero-warning automated test execution.
- **Full Documentation Suite**: Created root-level guides (`PHASE15_AUDIT.md`, `PHASE15.md`, `DEPLOYMENT.md`, `SECURITY.md`, `API.md`, `ENVIRONMENT.md`, `TROUBLESHOOTING.md`).
- **Automated Test Expansion**: Added `backend/tests/test_phase15_real_world_launch.py`, expanding total verified tests to **188 PASSED, 0 FAILED** (100% Pass Rate).

### Phase 14: Production Deployment & Real-World QA
- **End-to-End System Integration**: Unified flow from Citizen SOS to AI Priority Triage, SPHERE Resource Forecasting, Volunteer Matching, QR Proof-of-Delivery, Cryptographic Merkle Ledger Sealing, and AI Copilot Summarization.
- **Production Hardening**: Enforced 32+ character secrets, non-wildcard CORS validation, non-root Docker execution, and structured JSON logging.
- **Architecture Documentation**: Comprehensive multi-layer design specification in `docs/ARCHITECTURE.md`.

### Phase 13: Final QA & Release Candidate
- **Root-Level Execution**: Dynamic `sys.path` auto-resolution enabling direct execution from repository root (`py -3 -m uvicorn backend.app.main:app`).
- **Database Schema Auto-Sync**: Non-destructive PRAGMA column auto-sync for SQLite development environments on startup.
- **Release Verification**: Verified complete release checklist (`docs/release-checklist.md`).

### Phase 12: Production UX, Mobile & PWA Polish
- **Progressive Web App (PWA)**: Enhanced Web App Manifest (`frontend/manifest.json`) with app shortcuts (`One-Tap SOS`, `Citizen Hub`, `Volunteer Ops`, `AI Copilot`).
- **Offline Reliability**: Service Worker background sync listener (`sync-offline-sos`) and dynamic connectivity states (`ONLINE`, `OFFLINE`, `SYNCING`).

### Phase 11: Modular Web Application Integration
- **Frontend Architecture**: Modular React + TypeScript structure (`src/types/`, `src/services/`, `src/context/`, `src/pages/`, `src/layouts/`).
- **API & WebSocket Client**: Centralized Axios client with automatic JWT token attachment, 401 interceptor, and auto-reconnecting WebSocket gateway.

### Phase 10: Interactive UI/UX & Smart Systems
- **AI Disaster Copilot**: Conversational operational assistant with prompt chips, telemetry-verified citations, and clear data source badges.
- **Disaster Digital Twin**: Interactive scenario modeler with dynamic sliders (Severity, Population, Radius, Horizon) and SPHERE resource burn rate calculations.
- **SPHERE Shortage Radar**: Multi-horizon supply buffer gauge with color-coded deficit cards (`GREEN`, `YELLOW`, `ORANGE`, `RED`).
- **Cryptographic Transparency Journey**: Public verifiable 6-stage delivery pipeline with SHA-256 Merkle block proofs.

### Phase 9: Multi-Hazard Disaster Intelligence
- **Ingestion Engine**: Multi-provider disaster event stream normalization with fingerprint deduplication.
- **Incident State Machine**: Lifecycle transitions (`DETECTED` $\rightarrow$ `VERIFIED` $\rightarrow$ `ACTIVE` $\rightarrow$ `CONTAINED` $\rightarrow$ `RESOLVED`).

### Phase 8: Advanced AI Decision Support
- **AI Model Registry**: Versioned Scikit-Learn `RandomForestClassifier` (`v2.4.0-phase8`) with `<10ms` inference latency.
- **Explainable AI (XAI)**: Feature attribution vectors and plain-English factor breakdowns.
- **4-Factor Volunteer Matching**: Multi-criteria ranking across distance, skills, capacity, and reliability score.

### Phase 7: Cloud DevOps & Disaster Recovery
- **Containerization**: Multi-stage Dockerfile and Docker Compose production service stack with PostgreSQL 16.
- **Reverse Proxy**: Nginx configuration with SSL termination and WebSocket upgrade headers.
- **Automated Backup & Recovery**: Database backup and restore scripts with SHA-256 integrity validation.
- **Observability**: Prometheus OpenMetrics telemetry (`/metrics`) and Kubernetes-compatible health probes (`/health/live`, `/health/ready`).

### Phase 5–6: Geospatial, Operations & Security Hardening
- **Geospatial Proximity**: Haversine distance calculations, hotspot detection, and privacy location fuzzing.
- **Security Middleware**: Authenticated WebSockets, sliding-window rate limiting, and correlation `X-Request-ID` tracing.

### Phase 1–4: Core Platform Foundation
- **Identity & Access**: JWT authentication and Role-Based Access Control (Citizen, Volunteer, NGO, Donor, Admin).
- **Core Operations**: Emergency SOS relief requests, mission dispatch, warehouse inventory management.
- **Proof-of-Delivery**: Single-use cryptographic QR code verification tokens.
- **Tamper-Evident Ledger**: Merkle-linked sequential SHA-256 block chain.
