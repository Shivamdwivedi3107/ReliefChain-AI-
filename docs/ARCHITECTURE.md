# ReliefChain AI — System Architecture & Layered Technical Specification

## 1. System Overview

**ReliefChain AI** is an intelligent humanitarian aid coordination, AI-powered emergency triage, SPHERE resource deficit forecasting, single-use QR proof-of-delivery, and cryptographic audit ledger platform.

```
+-----------------------------------------------------------------------------------+
|                         PRESENTATION & CLIENT LAYER                               |
|  - Modern PWA & Responsive Web Client (Standalone Display, Touch UX)             |
|  - Modular React + TypeScript Frontend (`frontend/src/`)                          |
|  - Vanilla Glassmorphism Static Web App (`frontend/` mounted at `/ui/`)           |
|  - Role Portals: Citizen Hub, Field Volunteer Ops, Admin Command Center, NGO, Donor|
|  - Real-Time WebSocket Gateway (`/ws`), Reconnecting Telemetry Listener           |
|  - Offline Service Worker Cache & Safe Offline Action Queue (`sync-offline-sos`)  |
+-----------------------------------------------------------------------------------+
                                         │ REST (JSON) / WebSockets
                                         ▼
+-----------------------------------------------------------------------------------+
|                      FASTAPI APPLICATION & SECURITY GATEWAY                       |
|  - Security & Auth Middleware: JWT Bearer Tokens (HS256), Multi-Role RBAC Guards  |
|  - Request ID Tracing: `X-Request-ID` correlation header injected into all logs   |
|  - Sliding-Window In-Memory Rate Limiter (IP-based quotas)                        |
|  - Structured Logging & Sensitive Data Masking (passwords, tokens, credentials)   |
|  - CORS Whitelist & Trusted Host Verification                                     |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                            DOMAIN BUSINESS SERVICES                               |
|  - Ingestion Engine: Multi-source disaster stream normalization & deduplication   |
|  - Incident Lifecycle: State machine (`DETECTED` -> `ACTIVE` -> `RESOLVED`)       |
|  - Disaster Escalation Engine: Threat analysis & SITREP reporting                 |
|  - SPHERE Logistics Engine: International humanitarian standard burn calculators  |
|  - 4-Factor Volunteer Matching: Distance, Skills, Capacity & Reliability ranker   |
|  - AI Decision Support: Scikit-Learn RandomForest Model Registry (`v2.4.0`)      |
|  - Explainable AI (XAI): Feature attribution vectors and plain-English reasons    |
|  - AI Disaster Copilot: Contextual operational assistant with verified citations  |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
|                        PERSISTENCE & CRYPTOGRAPHIC LEDGER                         |
|  - SQLAlchemy 2.0 ORM: PostgreSQL 16 (Production) / SQLite (Local Fallback)       |
|  - Tamper-Evident SHA-256 Merkle Ledger: Sequential block audit chain             |
|  - Single-Use QR Verifier: Cryptographic nonce burn with GPS coordinate capture   |
|  - Observability: Prometheus OpenMetrics (`/metrics`), Health (`/health/ready`)   |
+-----------------------------------------------------------------------------------+
```

---

## 2. Layer-by-Layer Architectural Deep Dive

### 2.1 Presentation & Progressive Web App (PWA) Layer
- **Client Architecture**: Clean separation between modular React+TypeScript frontend (`frontend/src/`) and production-ready static single-page application (`frontend/index.html`, `frontend/js/app.js`, `frontend/css/styles.css`).
- **PWA Capabilities**: Served via `manifest.json` with standalone display modes, orientation overrides, app shortcuts (`One-Tap SOS`, `Citizen Hub`, `Volunteer Ops`, `AI Copilot`), and `sw.js` offline caching.
- **Dynamic Connectivity State**: UI continuously monitors network state and presents clear badges:
  - `🟢 ONLINE`: Full REST and WebSocket real-time event streaming.
  - `🔴 OFFLINE`: Cached shell, local incident catalog, and offline SOS queue.
  - `🟡 SYNCING`: Background replay of queued emergency requests via Service Worker sync.

### 2.2 Security & Access Control Layer
- **Authentication**: Stateless JSON Web Tokens (JWT) signed with HMAC-SHA256 containing user subject ID, role, and expiration claims.
- **Role-Based Access Control (RBAC)**:
  - `citizen`: Create SOS relief requests, view personal distress tickets, locate safe evacuation shelters, calculate pre-flight triage scores.
  - `volunteer`: View active assignments, track workload capacity meters, scan single-use QR delivery tokens, review 4-factor AI match recommendations.
  - `ngo`: Manage depot inventories, allocate supply bundles, track donation receipts.
  - `donor`: View public verifiable aid journey, review SHA-256 Merkle block proofs.
  - `admin`: Full Command Center authority, threat grid escalations, AI model registry activation, disaster simulation sandbox.

### 2.3 AI Intelligence & Decision Support Layer
- **Dual-Layer Random Forest Triage**:
  - Model registry loads versioned Scikit-Learn `RandomForestClassifier` (`v2.4.0-phase8`) trained on humanitarian disaster features (disaster severity, affected population, food/water/medical urgency flags, vulnerable demographics).
  - Sub-millisecond inference time (`<10ms`).
- **Explainable AI (XAI)**:
  - Computes normalized feature importance weights and plain-English factor breakdowns (e.g. `Critical Medical Need (+42%)`, `Severely Affected Count (+28%)`).
- **SPHERE Logistics Engine**:
  - Evaluates relief demands against international humanitarian standards:
    - **Drinking Water**: $15\text{ Liters / person / day}$
    - **Food Rations**: $3\text{ High-calorie packs / person / day}$
    - **Medical Kits**: $0.05\text{ Surgical trauma kits / person / day}$
  - Compares required demand against active depot inventories to calculate immediate replenishment deficits.

### 2.4 Cryptographic Proof-of-Delivery & Tamper-Evident Ledger
- **Sequential Block Chain**:
  - Every aid state transition (Donation Received $\rightarrow$ Inventory Allocated $\rightarrow$ Mission Dispatched $\rightarrow$ Physical QR Handover) generates a cryptographic record hash:
    $$H_n = \text{SHA256}(H_{n-1} \parallel \text{reference\_id} \parallel \text{event\_type} \parallel \text{payload} \parallel \text{timestamp})$$
  - The chain is verified via `/api/v1/blockchain/verify-chain`, which validates that every block's `previous_hash` matches the preceding block's `record_hash`.
- **Single-Use QR Verification**:
  - Generates a one-time cryptographic token burned upon physical delivery confirmation, capturing GPS coordinates and responder timestamp to eliminate duplicate aid claims.

### 2.5 Real-Time WebSocket & Observability Gateway
- **WebSocket Hub**: Broadcasts live disaster updates, distress escalations, and mission status changes without requiring client-side page refreshes.
- **Telemetry & Monitoring**:
  - `/health/live`: Lightweight process liveness check.
  - `/health/ready`: Deep dependency readiness probe verifying database connectivity, AI model readiness, and ledger status.
  - `/metrics`: Prometheus OpenMetrics endpoint tracking request rates, HTTP status codes, and execution latencies.
