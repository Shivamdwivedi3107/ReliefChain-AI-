# ReliefChain AI — API Documentation Reference

Refer to [docs/API_GUIDE.md](file:///c:/Users/USER/Desktop/Reliefchain%20AI/docs/API_GUIDE.md) for the complete endpoint schema and request payload guide.

### Primary API Endpoints Index

| Tag | Prefix | Sample Endpoints |
| :--- | :--- | :--- |
| **Authentication** | `/api/v1/auth` | `POST /register`, `POST /login`, `GET /me` |
| **Relief Requests** | `/api/v1/relief-requests` | `POST /`, `GET /`, `GET /{id}`, `POST /{id}/assign` |
| **Incidents** | `/api/v1/incidents` | `POST /`, `GET /`, `POST /{id}/verify`, `POST /{id}/activate` |
| **Resources & SPHERE**| `/api/v1/resources` | `GET /`, `GET /inventory/list`, `GET /shortage-radar` |
| **Volunteer Matching**| `/api/v1/volunteers` | `POST /recommendations`, `GET /nearby` |
| **Blockchain Ledger** | `/api/v1/blockchain` | `GET /transactions`, `GET /verify-chain` |
| **AI Copilot** | `/api/v1/copilot` | `GET /suggested-prompts`, `POST /query` |
| **Observability** | `/` | `GET /health`, `GET /health/live`, `GET /health/ready`, `GET /metrics` |
| **Web UI & PWA** | `/ui` | `GET /ui/`, `GET /ui/manifest.json`, `GET /ui/sw.js` |
