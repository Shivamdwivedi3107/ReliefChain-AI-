# ReliefChain AI — Complete REST & WebSocket API Specification

**Base URL**: `http://127.0.0.1:8000/api/v1`  
**Swagger UI**: `http://127.0.0.1:8000/docs`  
**ReDoc**: `http://127.0.0.1:8000/redoc`  
**WebSocket Gateway**: `ws://127.0.0.1:8000/ws`  

---

## 1. Authentication & Identity Management

| Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `/auth/register` | `POST` | Public | Register a new citizen, volunteer, NGO, or donor account. |
| `/auth/login` | `POST` | Public | Authenticate via email & password to receive signed JWT bearer token. |
| `/auth/me` | `GET` | Authenticated | Retrieve current session profile, active role, and permissions. |

---

## 2. Emergency Relief Requests & AI Triage

| Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `/relief-requests` | `POST` | `citizen`, `admin` | Create emergency SOS distress ticket with automated AI priority inference (`critical`, `high`, `medium`, `low`). |
| `/relief-requests` | `GET` | Authenticated | List paginated relief requests with optional status and priority filters. |
| `/relief-requests/{id}` | `GET` | Authenticated | Retrieve specific relief request details and explainable AI factors. |
| `/relief-requests/{id}/assign` | `POST` | `ngo`, `admin` | Assign field volunteer or organization to the relief mission. |

---

## 3. Multi-Hazard Incidents & Disaster Intelligence

| Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `/incidents` | `POST` | `ngo`, `admin` | Create a confirmed disaster incident with geolocation and initial radius. |
| `/incidents` | `GET` | Authenticated | Query active multi-hazard incidents with threat levels. |
| `/incidents/{id}/verify` | `POST` | `ngo`, `admin` | Transition incident state from `DETECTED` to `VERIFIED`. |
| `/incidents/{id}/activate` | `POST` | `ngo`, `admin` | Transition incident state to `ACTIVE` for real-time dispatch. |
| `/incidents/{id}/resolve` | `POST` | `ngo`, `admin` | Transition incident state to `RESOLVED`. |
| `/incidents/{id}/timeline` | `GET` | Authenticated | Chronological append-only audit timeline of incident events. |
| `/incidents/{id}/sitreps` | `POST` | `ngo`, `admin` | Submit an operational situation report (SITREP). |

---

## 4. SPHERE Logistics & Warehouse Inventory

| Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `/resources` | `GET` | Authenticated | List global catalog resource items (Water, Food, Medical, Shelter, Blankets). |
| `/resources/inventory/list`| `GET` | `ngo`, `admin` | List warehouse inventory balances across depots. |
| `/resources/inventory/{id}`| `PATCH` | `ngo`, `admin` | Update warehouse inventory quantities with strict negative value guards. |
| `/resources/shortage-radar`| `GET` | Authenticated | SPHERE international standard buffer gauge calculating immediate deficit gaps. |

---

## 5. 4-Factor AI Volunteer Matching

| Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `/volunteers/recommendations` | `POST` | `ngo`, `admin` | Rank suitable volunteers using 4-factor scoring (Distance 35%, Skills 30%, Capacity 20%, Reliability 15%). |

---

## 6. Cryptographic Proof-of-Delivery & Tamper-Evident Ledger

| Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `/donations` | `POST` | `donor`, `admin` | Record financial or physical resource donation. |
| `/blockchain/transactions` | `GET` | Authenticated | List verifiable Merkle block transactions. |
| `/blockchain/verify-chain` | `GET` | `admin` | Verify cryptographic SHA-256 sequential hash integrity across the full ledger. |
| `/transparency/latest-journeys` | `GET` | Public | Public 6-stage end-to-end aid delivery timeline with block hashes. |

---

## 7. AI Disaster Copilot & Decision Support

| Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `/copilot/suggested-prompts` | `GET` | Authenticated | Suggested situational prompts for rapid dispatch guidance. |
| `/copilot/query` | `POST` | Authenticated | Natural language query processing with telemetry citations and actionable directives. |

---

## 8. System Health, Telemetry & Diagnostics

| Endpoint | Method | Role Required | Description |
| :--- | :--- | :--- | :--- |
| `/health` | `GET` | Public | General system health check verifying database connectivity. |
| `/health/live` | `GET` | Public | Kubernetes/supervisor process liveness probe. |
| `/health/ready` | `GET` | Public | Deep readiness probe validating database, AI model registry, and storage. |
| `/metrics` | `GET` | Public | Prometheus OpenMetrics telemetry endpoint. |
| `/ui/manifest.json` | `GET` | Public | PWA installation manifest with quick-action shortcuts. |
| `/ui/sw.js` | `GET` | Public | Offline caching service worker with background sync queue. |
