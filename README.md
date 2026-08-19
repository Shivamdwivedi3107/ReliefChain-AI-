# ReliefChain AI 🌐⚡

> **Intelligent Humanitarian Aid Coordination, AI Emergency Triage, and Blockchain-Inspired Transparency Ledger**

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Pytest](https://img.shields.io/badge/Tests-19%20Passed-brightgreen.svg?logo=pytest)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 1. Project Overview
**ReliefChain AI** is a comprehensive, production-style disaster response and resource coordination platform. It unifies community SOS emergency intakes, AI-assisted decision support triage, warehouse inventory locking, and cryptographic proof-of-delivery into a verifiable, closed-loop humanitarian relief pipeline.

---

## 2. Problem Statement
During major natural catastrophes (floods, earthquakes, cyclones, wildfires):
1. **Triage Bottlenecks**: Emergency responders are overwhelmed with thousands of disparate requests and lack standardized, transparent priority scoring.
2. **Aid Wastage & Over-Allocation**: Relief warehouses frequently run out of critical supplies due to uncoordinated duplicate dispatches.
3. **Delivery Fraud & Phantom Deliveries**: Without verifiable proof-of-handover, aid supplies are vulnerable to misplacement or diversion.
4. **Lack of Donor Trust**: Donors cannot trace whether their funds or supplies reached the intended beneficiaries.

---

## 3. The Solution
- **Citizen SOS Intake**: Geolocation-tagged emergency submissions with multi-resource requirement checklists.
- **AI Decision Support System (DSS)**: Rule-based, transparent 0–100 emergency priority scoring engine alongside a trained Random Forest classifier (`87% accuracy`) factoring disaster severity, medical trauma, trapped populations, and waiting time.
- **Depot Inventory Management**: Real-time warehouse tracking with hard over-allocation prevention and low-stock alerts.
- **Single-Use Cryptographic QR Tokens**: Dynamic QR verification codes generated per mission.
- **Volunteer Handover Verification**: GPS-stamped field confirmation preventing duplicate redemption.
- **Tamper-Evident Ledger**: Sequential Merkle-linked block hashing providing permanent auditability with optional EVM/Web3 smart contract connectivity.

---

## 4. Key Application Screenshots

| Screen | Description |
| :--- | :--- |
| **Landing & Public Overview** | Hero showcase, live global impact metrics, and 4-step humanitarian pipeline visualizer. |
| **Emergency Mission Control** | Real-time operations center with urgent triage queue and quick dispatch actions. |
| **Citizen SOS Intake & AI Triage** | Emergency form with real-time AI priority score and triage level calculation. |
| **Warehouse Inventory Depot** | Supply stock levels (available vs reserved), low-stock warning banners, and replenishment modal. |
| **Distributions & Cryptographic QR** | Mission dispatching, Base64 PNG QR token generation, and volunteer field delivery simulator. |
| **Blockchain Transparency Ledger** | SHA-256 Merkle block explorer with 1-click cryptographic whole-chain integrity auditor. |
| **Humanitarian Analytics Visualizer** | Live dynamic SVG charts (disasters by type, priority distribution, lifecycle statuses). |
| **Interactive API Documentation** | OpenAPI Swagger UI (`/docs`) and ReDoc (`/redoc`) for all endpoints. |

---

## 5. System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Modern Frontend (SPA)                    │
│   Landing • Mission Control • Requests • Inventory Depot    │
│      Distributions & QR • Ledger Explorer • Analytics       │
└──────────────────────────────┬──────────────────────────────┘
                               │ REST / JSON (JWT Authenticated)
┌──────────────────────────────▼──────────────────────────────┐
│                    FastAPI Backend Router                   │
│   Auth & RBAC • Requests • Inventory • QR • Ledger • Stats  │
└───────┬──────────────────────┬──────────────────────┬───────┘
        │                      │                      │
┌───────▼────────┐     ┌───────▼────────┐     ┌───────▼───────┐
│ AI Triage DSS  │     │ SQL Database   │     │ Tamper-Evident│
│ Rule/ML Engine │     │ Relational ORM │     │ Merkle Ledger │
└────────────────┘     └────────────────┘     └───────────────┘
```

---

## 6. Technology Stack
- **Backend API**: Python 3, FastAPI, Uvicorn, Pydantic v2
- **Database & ORM**: PostgreSQL / SQLite fallback, SQLAlchemy 2.0
- **Security & Authentication**: JWT (JSON Web Tokens), Passlib (Argon2 / BCrypt), OAuth2 Bearer
- **AI / DSS Prioritization**: Decision Support Scoring Engine & Scikit-learn Random Forest Classifier
- **Cryptographic Transparency**: SHA-256 Merkle Chain Ledger, Web3.py / EVM Mock-to-Contract Bridge
- **QR Code Engine**: Base64 dynamic QR Code generation with single-use crypto-token validation
- **Frontend**: HTML5, Vanilla CSS Glassmorphism Design System, Modular JavaScript, SVG Data Visualizations
- **Testing**: Pytest (19 comprehensive automated test cases with 100% pass rate)

---

## 7. Project Directory Structure
```
Reliefchain AI/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration, security, logging
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── routes/         # REST API routers
│   │   ├── schemas/        # Pydantic validation schemas
│   │   ├── services/       # AI triage, blockchain ledger, QR services
│   │   ├── database.py     # SessionLocal, Base, engine initialization
│   │   ├── dependencies.py # Role-based access control (RBAC)
│   │   ├── seed.py         # Database auto-seed script
│   │   └── main.py         # FastAPI application entrypoint
│   ├── tests/              # 19 Pytest automated test suites
│   ├── requirements.txt    # Python dependencies
│   └── alembic/            # Database migrations
├── frontend/
│   ├── index.html          # Single Page Application dashboard
│   ├── css/styles.css      # Glassmorphism dark-mode styles
│   └── js/
│       ├── api.js          # Centralized API service
│       └── app.js          # Controller & view state logic
├── ai/
│   ├── dataset/            # Historical disaster datasets
│   ├── model/              # Serialized ML model artifacts (.joblib)
│   ├── train.py            # Model training pipeline
│   └── evaluate.py         # Evaluation scripts
├── blockchain/
│   ├── contracts/          # Solidity smart contracts
│   └── hardhat.config.js   # Hardhat EVM environment
├── PROJECT_STATUS.md       # Audit matrix and component status
├── .env.example            # Environment variables template
├── pytest.ini              # Pytest configuration
└── README.md               # Master project documentation
```

---

## 8. Installation & Quick Start

### 1. Backend Setup
```bash
cd backend
python -m venv venv
# Windows:
.\venv\Scripts\Activate.ps1
# Linux/macOS:
# source venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration
Copy the `.env.example` file:
```bash
cp .env.example backend/.env
```

### 3. Run Development Server
```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **API Base**: `http://localhost:8000/api/v1`
- **Interactive Swagger Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`
- **Frontend Web UI**: `http://localhost:8000/ui/`

---

## 9. Demo Accounts & Credentials

The application auto-seeds demo credentials for each role (Password: `SecurePassword123!`):

| Role | Email | Permissions |
| :--- | :--- | :--- |
| **Administrator** | `admin@reliefchain.ai` | Full system control and administration |
| **Relief Org (NGO)** | `ngo@reliefchain.ai` | Manage warehouse stock & dispatch distributions |
| **Field Volunteer** | `volunteer1@reliefchain.ai` | Scan & confirm cryptographic QR handovers in the field |
| **Citizen** | `shivam@reliefchain.ai` | Submit SOS emergency requests & view status |
| **Donor** | `donor@reliefchain.ai` | Contribute monetary/physical aid & track ledger hashes |

---

## 10. Running Automated Tests
Run the 19 automated test cases covering Auth, Roles, Relief Requests, AI Triage, Inventory, Over-Allocation, QR Verification, and Ledger Chain Integrity:
```bash
py -3 -m pytest
```
Output:
```text
============================= 19 passed in 10.92s =============================
backend/tests/test_ai_prioritization.py ....                             [ 21%]
backend/tests/test_auth.py .....                                         [ 47%]
backend/tests/test_distributions_and_qr.py .                             [ 52%]
backend/tests/test_donations_and_ledger.py .                             [ 57%]
backend/tests/test_health.py ..                                          [ 68%]
backend/tests/test_models.py .                                           [ 73%]
backend/tests/test_relief_requests.py .                                  [ 78%]
backend/tests/test_resources_and_inventory.py ..                         [ 89%]
backend/tests/test_roles_and_permissions.py ..                           [100%]
```

---

## 11. API Reference Summary

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register citizen, volunteer, NGO, donor, or admin | Public |
| `POST` | `/api/v1/auth/login` | Obtain JWT Bearer Token | Public |
| `GET` | `/api/v1/auth/me` | Current authenticated user profile | Authenticated |
| `GET` | `/api/v1/relief-requests` | List relief requests with filters & urgency sorting | Public |
| `POST` | `/api/v1/relief-requests` | Submit SOS request with automatic AI triage scoring | Authenticated |
| `POST` | `/api/v1/relief-requests/{id}/assign` | Assign NGO and Volunteer to mission | NGO / Admin |
| `DELETE`| `/api/v1/relief-requests/{id}` | Cancel/delete relief request | Owner / Admin |
| `POST` | `/api/v1/ai/predict-priority` | AI DSS triage priority evaluation (0-100 score) | Public |
| `GET` | `/api/v1/resources` | Resource catalog items | Public |
| `POST` | `/api/v1/resources/inventory` | Add/restock warehouse inventory | NGO / Admin |
| `GET` | `/api/v1/resources/alerts/low-stock`| Inventory low stock threshold alerts | Public |
| `POST` | `/api/v1/distributions` | Dispatch distribution (locks inventory stock) | NGO / Admin |
| `POST` | `/api/v1/qr/generate/{dist_id}` | Generate dynamic Base64 QR code image & token | Public |
| `POST` | `/api/v1/qr/confirm` | Volunteer confirms GPS delivery (tamper-proof) | Volunteer / Admin |
| `POST` | `/api/v1/donations` | Create monetary or in-kind supplies donation | Public |
| `GET` | `/api/v1/ledger` | List Merkle-linked audit blocks | Public |
| `GET` | `/api/v1/ledger/{id}` | Inspect individual ledger transaction | Public |
| `GET` | `/api/v1/ledger/verify` | Verify entire ledger cryptographic chain integrity | Public |

---

## 12. Technology Distinctions & Design Honesty
- **AI Capabilities**: The system implements an **Emergency Decision Support System (DSS)** triage engine calculating transparent 0–100 scores based on weighted factors (disaster type, casualty counts, medical trauma, potable water needs, vulnerable populations, location hazard, and waiting time decay). Alongside the DSS, a trained Scikit-learn Random Forest classifier (`87% accuracy`) is saved in `ai/model/priority_classifier.joblib`.
- **Transparency Ledger**: Built with a **tamper-evident SHA-256 Merkle-linked block chain** abstraction verified through `/ledger/verify`. In local/test mode, blocks are deterministically hashed with previous-hash linkages. When configured with RPC credentials, it bridges to EVM smart contracts (`blockchain/contracts`).

---

## 13. Future Enhancements
- Live decentralized IPFS storage for damage assessment photos.
- Geofenced automated volunteer proximity verification.
- Offline-first ServiceWorker support for disconnected field disaster zones.
- Real-time WebSockets notification streams for volunteer dispatch.
