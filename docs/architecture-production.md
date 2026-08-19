# ReliefChain AI — Production Architecture & Telemetry

This document describes the high-level infrastructure topology, data flow, telemetry pipelines, and scaling characteristics of ReliefChain AI.

---

## 1. System Architecture Diagram

```text
                                  [ Internet / Mobile Beneficiaries ]
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Edge Layer: Nginx Reverse Proxy                               │
│  - HTTPS / TLS Termination (Port 443)                                                           │
│  - Static PWA Shell & Asset Caching (/ui/, /uploads/)                                           │
│  - WebSocket Connection Upgrade (/ws/notifications)                                             │
│  - Security Headers (nosniff, DENY, Referrer-Policy)                                            │
│  - Upstream Load Balancing & Buffer Management                                                  │
└──────────────────────────────────────────────────┬──────────────────────────────────────────────┘
                                                   │
                                                   ▼
┌─────────────────────────────────────────────────────────────────────────────────────────────────┐
│                                FastAPI ASGI Application Cluster (Workers)                       │
│  - Request ID Tracing (X-Request-ID) & Timing (X-Process-Time-Ms)                               │
│  - Role-Based Access Control (RBAC) & JWT Middleware                                            │
│  - Sliding Window In-Memory Rate Limiting                                                       │
│  - Dual-Layer AI DSS & Scikit-Learn Random Forest Classifier                                    │
│  - Geographic Intelligence & 25km Hotspot Clustering Engine                                     │
│  - Exception-Isolated Background Task Executor                                                  │
│  - OpenMetrics / Prometheus Telemetry Engine (/metrics)                                         │
└──────────────────────────────────┬───────────────────────────────┬──────────────────────────────┘
                                   │                               │
                                   ▼                               ▼
┌──────────────────────────────────────────────┐ ┌────────────────────────────────────────────────┐
│   PostgreSQL 16 Relational Database Engine   │ │     SHA-256 Merkle Transparency Ledger         │
│  - Connection Pool (pool_size=10, max=20)    │ │  - Cryptographically linked transaction blocks │
│  - Pre-Ping Connection Health Checks         │ │  - Previous-hash sequential integrity          │
│  - Single & Composite Performance Indexes    │ │  - Whole-chain verification endpoint           │
│  - Isolated Private Docker Network           │ │  - Optional Web3/EVM Smart Contract Bridge     │
└──────────────────────────────────────────────┘ └────────────────────────────────────────────────┘
```

---

## 2. Observability & Telemetry Metrics

The backend exposes a thread-safe OpenMetrics / Prometheus exporter on `GET /metrics`:

| Metric Name | Type | Description |
|---|---|---|
| `reliefchain_uptime_seconds` | Gauge | Total process runtime in seconds |
| `reliefchain_http_requests_total` | Counter | Cumulative HTTP request count |
| `reliefchain_http_errors_total` | Counter | Total 4xx and 5xx HTTP errors |
| `reliefchain_http_active_requests` | Gauge | Currently in-flight HTTP requests |
| `reliefchain_rate_limit_blocks_total` | Counter | Total rate limit throttle rejections |
| `reliefchain_auth_failures_total` | Counter | Total authentication & JWT validation rejections |

---

## 3. Health & Readiness Check Probes

- **Liveness Probe** (`GET /health/live`): Fast check returning `{"status": "alive"}` for container restart evaluation.
- **Deep Readiness Probe** (`GET /health/ready`): Deep subsystem inspection validating:
  - Database connectivity (SQL query execution)
  - AI model artifact availability and load state
  - Transparency ledger subsystem readiness
