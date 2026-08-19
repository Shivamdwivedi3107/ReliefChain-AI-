# ReliefChain AI — Backend Engine

FastAPI-powered RESTful API server for disaster relief management, AI triage scoring, blockchain ledger interaction, and cryptographic QR verification.

## Features
- **FastAPI Core**: Async, high-performance API routing with automatic OpenAPI documentation.
- **Pydantic Validation**: Strict request/response schema modeling and serialization.
- **PostgreSQL / SQLAlchemy ORM**: Robust relational data persistence with migration support.
- **Role-Based Access Control**: JWT authentication guarding endpoints for Citizens, NGOs, Volunteers, and Admins.
- **Web3.py Connector**: Immutable SHA-256 state hashing sent to EVM smart contracts.
- **Scikit-Learn DSS**: Decision Support System for emergency prioritization triage.

## Quick Start

### 1. Create and Activate Virtual Environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 3. Run Development Server
```powershell
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Interactive API Docs
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`
