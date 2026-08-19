# ReliefChain AI 🌐⚡

> **Intelligent Humanitarian Aid Coordination, AI Emergency Triage, and SHA-256 Hash-Linked Transparency Ledger**

[![Python Version](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi)](https://fastapi.tiangolo.com)
[![Pytest](https://img.shields.io/badge/Tests-19%20Passed-brightgreen.svg?logo=pytest)](https://pytest.org)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

---

## 1. Project Overview
**ReliefChain AI** is a comprehensive, production-style disaster response and humanitarian aid coordination platform. It unifies community SOS emergency intakes, AI-assisted decision support triage, warehouse inventory locking, and cryptographic proof-of-delivery into a verifiable, closed-loop relief pipeline.

---

## 2. Problem Statement
During natural disasters (floods, earthquakes, cyclones, wildfires):
1. **Triage Bottlenecks**: Emergency responders are inundated with thousands of disparate requests and lack standardized, transparent priority scoring.
2. **Aid Wastage & Over-Allocation**: Relief warehouses frequently run out of critical supplies due to uncoordinated duplicate dispatches.
3. **Delivery Fraud & Phantom Deliveries**: Without verifiable proof-of-handover, aid supplies are vulnerable to misplacement or diversion.
4. **Lack of Donor Trust**: Donors cannot trace whether their funds or physical supplies reached the intended beneficiaries.

---

## 3. The Solution
- **Citizen SOS Intake**: Geolocation-tagged emergency submissions with multi-resource requirement checklists.
- **Dual-Layer AI Triage**: A transparent 0–100 rule-based Decision Support System (DSS) triage engine alongside a trained Scikit-learn Random Forest classifier (`87% test accuracy`, `97% dataset accuracy`) evaluating disaster severity, medical trauma, trapped populations, and waiting time.
- **Depot Inventory Management**: Real-time warehouse tracking with hard over-allocation prevention and low-stock alerts.
- **Single-Use Cryptographic QR Tokens**: Dynamic Base64 QR verification codes generated per mission.
- **Volunteer Handover Verification**: GPS-stamped field confirmation preventing duplicate redemption.
- **SHA-256 Hash-Linked Ledger**: Sequential cryptographic block linking providing permanent auditability with optional EVM/Web3 smart contract connectivity.

---

## 4. Screenshots

Screenshots are organized in the `docs/screenshots/` directory:

| Screenshot | Description | File Path |
| :--- | :--- | :--- |
| **Landing & Public Overview** | Hero showcase, live global impact metrics, and 4-step humanitarian pipeline visualizer. | `docs/screenshots/01-landing-page.png` |
| **1-Click Role Switcher** | Instant demo authentication modal for Citizen, Volunteer, NGO, Donor, and Admin personas. | `docs/screenshots/02-login.png` |
| **Emergency Mission Control** | Operations center with urgent triage queue, active dispatches, and quick action controls. | `docs/screenshots/03-mission-control.png` |
| **Citizen SOS Intake** | Emergency form with real-time AI priority score and triage level calculation. | `docs/screenshots/04-sos-request.png` |
| **AI Decision Support Triage** | Granular factor explanations (medical trauma, trapped counts, hazard factors). | `docs/screenshots/05-ai-triage.png` |
| **Warehouse Inventory Depot** | Supply stock levels (available vs reserved), low-stock warning banners, and restocking. | `docs/screenshots/06-inventory.png` |
| **Distributions & QR Verification** | Mission dispatching, Base64 PNG QR generation, and volunteer field delivery simulator. | `docs/screenshots/07-distribution-qr.png` |
| **Transparency Ledger Explorer** | SHA-256 hash chain explorer with 1-click cryptographic whole-chain integrity auditor. | `docs/screenshots/08-ledger.png` |
| **Humanitarian Analytics** | Live dynamic SVG charts (disasters by type, priority distribution, lifecycle statuses). | `docs/screenshots/09-analytics.png` |

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
│ AI Triage DSS  │     │ SQL Database   │     │ SHA-256 Hash- │
│ Rule/ML Engine │     │ Relational ORM │     │ Linked Ledger │
└────────────────┘     └────────────────┘     └───────────────┘
```

---

## 6. Technology Stack
- **Backend API**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2
- **Database & ORM**: SQLite local fallback / PostgreSQL, SQLAlchemy 2.0, Alembic migrations
- **Security & Authentication**: JWT (JSON Web Tokens), Passlib (Argon2 / BCrypt), OAuth2 Bearer
- **AI & Decision Support**: Scikit-learn Random Forest Classifier (`joblib`) & rule-based DSS triage scoring
- **Cryptographic Transparency**: SHA-256 Sequential Hash-Linked Ledger, Web3.py / EVM Smart Contract Bridge (`Solidity`)
- **QR Code Engine**: Base64 dynamic PNG generation with single-use cryptographic token validation
- **Frontend**: HTML5, Vanilla CSS Glassmorphism Design System, Modular JavaScript, Dynamic SVG Data Visualizations
- **Testing**: Pytest (19 comprehensive automated test cases with 100% pass rate)

---

## 7. Project Directory Structure
```
Reliefchain AI/
├── backend/
│   ├── app/
│   │   ├── core/           # Configuration, security, logging
│   │   ├── models/         # SQLAlchemy database models
│   │   ├── routes/         # REST API route handlers
│   │   ├── schemas/        # Pydantic v2 validation schemas
│   │   ├── services/       # AI triage, blockchain ledger, QR services
│   │   ├── database.py     # Database engine & session initialization
│   │   ├── dependencies.py # Role-based access control (RBAC)
│   │   ├── seed.py         # Automated database seeding script
│   │   └── main.py         # FastAPI application entrypoint & static mount
│   ├── tests/              # 19 Pytest automated test suites
│   ├── requirements.txt    # Backend Python dependencies
│   └── alembic/            # Database migrations
├── frontend/
│   ├── index.html          # Single Page Application dashboard
│   ├── css/styles.css      # Glassmorphism dark-mode stylesheet
│   └── js/
│       ├── api.js          # Centralized API client service
│       └── app.js          # UI controller & application logic
├── ai/
│   ├── dataset/            # Historical disaster datasets (1500 records)
│   ├── model/              # Serialized Random Forest model artifact (.joblib)
│   ├── train.py            # Model training pipeline
│   └── evaluate.py         # Model evaluation & classification report
├── blockchain/
│   ├── contracts/          # Solidity smart contracts (ReliefChainLedger.sol)
│   └── hardhat.config.js   # Hardhat EVM testing configuration
├── docs/
│   └── screenshots/        # Application interface captures
├── PROJECT_STATUS.md       # Detailed audit matrix and status log
├── .env.example            # Environment variables template
├── pytest.ini              # Pytest configuration & warning filters
└── README.md               # Master repository documentation
```

---

## 8. Installation & Setup

### Prerequisites
- **Python**: Version 3.10, 3.11, 3.12, or 3.14
- **Node.js** (Optional, only needed for local Hardhat smart contract development)

### 1. Clone & Set Up Virtual Environment

**Windows PowerShell:**
```powershell
cd "c:\path\to\Reliefchain AI\backend"
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

**Linux / macOS:**
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Configure Environment Variables

**Windows PowerShell:**
```powershell
Copy-Item .env.example .env
```

**Linux / macOS:**
```bash
cp .env.example .env
```

### 3. Run Development Server
```powershell
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```
- **Frontend Dashboard**: `http://localhost:8000/ui/`
- **Swagger Interactive API Docs**: `http://localhost:8000/docs`
- **ReDoc Documentation**: `http://localhost:8000/redoc`

---

## 9. Demo Accounts & Role Permissions

> [!IMPORTANT]
> **Security Notice**: The demo accounts listed below are automatically seeded strictly for local development and portfolio demonstration. Change or disable them prior to any production deployment.

| Role | Email | Password | Permissions |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@reliefchain.ai` | `SecurePassword123!` | Full system control and audit verification |
| **Relief Org (NGO)** | `ngo@reliefchain.ai` | `SecurePassword123!` | Warehouse inventory management & mission dispatch |
| **Field Volunteer** | `volunteer1@reliefchain.ai` | `SecurePassword123!` | Scan & confirm cryptographic QR handovers in the field |
| **Citizen** | `shivam@reliefchain.ai` | `SecurePassword123!` | Submit SOS emergency requests & track status |
| **Donor** | `donor@reliefchain.ai` | `SecurePassword123!` | Contribute monetary/physical aid & inspect ledger hashes |

---

## 10. Automated Testing

The project contains 19 comprehensive automated test cases across 9 test files.

Run the test suite from the project root:
```powershell
py -3 -m pytest
```

Test Results:
```text
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
configfile: pytest.ini
testpaths: backend/tests
collected 19 items

backend/tests/test_ai_prioritization.py ....                             [ 21%]
backend/tests/test_auth.py .....                                         [ 47%]
backend/tests/test_distributions_and_qr.py .                             [ 52%]
backend/tests/test_donations_and_ledger.py .                             [ 57%]
backend/tests/test_health.py ..                                          [ 68%]
backend/tests/test_models.py .                                           [ 73%]
backend/tests/test_relief_requests.py .                                  [ 78%]
backend/tests/test_resources_and_inventory.py ..                         [ 89%]
backend/tests/test_roles_and_permissions.py ..                           [100%]

============================= 19 passed in 10.92s =============================
```

---

## 11. REST API Reference

| Method | Endpoint | Description | Access |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/auth/register` | Register citizen, volunteer, NGO, donor, or admin | Public |
| `POST` | `/api/v1/auth/login` | Authenticate & obtain JWT Bearer Token | Public |
| `GET` | `/api/v1/auth/me` | Retrieve current authenticated user profile | Authenticated |
| `GET` | `/api/v1/relief-requests` | List relief requests with filters & urgency sorting | Public |
| `POST` | `/api/v1/relief-requests` | Submit SOS request with automatic AI triage scoring | Authenticated |
| `PATCH`| `/api/v1/relief-requests/{id}` | Update relief request status or attributes | NGO / Admin |
| `POST` | `/api/v1/relief-requests/{id}/assign` | Assign NGO and Volunteer to mission | NGO / Admin |
| `DELETE`| `/api/v1/relief-requests/{id}` | Cancel/delete relief request | Owner / Admin |
| `POST` | `/api/v1/ai/predict-priority` | AI DSS triage priority evaluation (0–100 score) | Public |
| `GET` | `/api/v1/resources` | List catalog resource items | Public |
| `POST` | `/api/v1/resources/inventory` | Add/restock warehouse inventory | NGO / Admin |
| `GET` | `/api/v1/resources/alerts/low-stock`| Retrieve low-stock inventory warnings | Public |
| `POST` | `/api/v1/distributions` | Dispatch distribution (locks inventory stock) | NGO / Admin |
| `POST` | `/api/v1/qr/generate/{dist_id}` | Generate dynamic Base64 QR code image & token | Public |
| `POST` | `/api/v1/qr/confirm` | Volunteer confirms GPS delivery (tamper-proof) | Volunteer / Admin |
| `POST` | `/api/v1/donations` | Create monetary or in-kind supplies donation | Public |
| `GET` | `/api/v1/ledger` | List SHA-256 hash-linked audit blocks | Public |
| `GET` | `/api/v1/ledger/{id}` | Inspect individual ledger transaction | Public |
| `GET` | `/api/v1/ledger/verify` | Verify entire ledger cryptographic chain integrity | Public |
| `POST` | `/api/v1/blockchain/verify` | Verify individual record hash against ledger | Public |
| `GET` | `/api/v1/analytics/summary` | Global summary metrics (requests, inventory, deliveries) | Public |

---

## 12. Technical Distinctions & Design Honesty

- **Decision Support System (DSS) vs. Machine Learning**:
  - The live production triage engine implements an **Emergency Decision Support System (DSS)** that computes an interpretable 0–100 score based on explicit, transparent factors: disaster type base risk, casualty counts, medical urgency, potable water needs, vulnerable populations, location hazard, and waiting time decay.
  - In addition, an experimental **Random Forest Classifier** trained on 1,500 historical disaster reports is provided in `ai/model/priority_classifier.joblib`, achieving **87.00% cross-validated test accuracy** (and **97.07% overall dataset accuracy** evaluated in `ai/evaluate.py`).
- **Tamper-Evident Ledger vs. Decentralized Blockchain**:
  - The core ledger operates as an on-database **SHA-256 sequential hash-linked chain** (each block hashes its payload together with the `previous_hash`), verified cryptographically via `GET /api/v1/ledger/verify`.
  - An optional **Web3 / EVM bridge** (`blockchain/contracts/ReliefChainLedger.sol`) is included for environments configured with an Ethereum RPC endpoint and private key.

---

## 13. Known Limitations
- The current database uses SQLite for seamless local sandbox execution; production deployments should point `DATABASE_URL` to a managed PostgreSQL instance.
- QR proof-of-delivery GPS coordinates rely on browser/client submission.
- IPFS storage for disaster site imagery is architected as an optional external layer.

---

## 14. Future Enhancements
- Live decentralized IPFS storage for damage assessment photos.
- Geofenced automated volunteer proximity verification using device GPS.
- Offline-first ServiceWorker support for disconnected field disaster zones.
- Real-time WebSockets notification streams for volunteer dispatch.

---

## 15. License
Distributed under the MIT License. See `LICENSE` for details.
