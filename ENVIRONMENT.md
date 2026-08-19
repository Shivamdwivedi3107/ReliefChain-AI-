# ReliefChain AI — Environment Variables Dictionary

This document details all configuration parameters loaded from `.env` or system environment variables.

---

## 1. Application & Core Runtime

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `PROJECT_NAME` | string | `"ReliefChain AI"` | Application display name. |
| `API_V1_STR` | string | `"/api/v1"` | URL prefix for REST API endpoints. |
| `ENVIRONMENT` | string | `"development"` | Options: `development`, `testing`, `staging`, `production`. |
| `DEBUG` | boolean | `True` | Must be `False` in production. |
| `HOST` | string | `"0.0.0.0"` | Host binding interface. |
| `PORT` | integer | `8000` | Port binding number. |
| `WORKERS` | integer | `4` | Number of ASGI Uvicorn worker processes. |

---

## 2. Security & Tokens

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `SECRET_KEY` | string | *Required* | Minimum 32-character secret key for JWT signatures and hashing. |
| `JWT_SECRET_KEY` | string | `""` | Optional override key for JWT signing. |
| `JWT_ALGORITHM` | string | `"HS256"` | JWT signature algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | integer | `1440` | JWT validity window in minutes (default: 24h). |

---

## 3. Database Persistence

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `DATABASE_URL` | string | `"sqlite:///./reliefchain.db"` | Primary database connection string. |
| `TEST_DATABASE_URL` | string | `"sqlite:///:memory:"` | In-memory database URL for automated testing. |

---

## 4. Cross-Origin Resource Sharing (CORS) & Rate Limiting

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `BACKEND_CORS_ORIGINS` | string | `"http://localhost:8000,http://127.0.0.1:8000"` | Comma-separated list of allowed origins. |
| `RATE_LIMIT_ENABLED` | boolean | `True` | Toggles sliding-window IP rate limiting. |
| `RATE_LIMIT_LOGIN_PER_MINUTE` | integer | `15` | Max login attempts per minute per IP. |
| `RATE_LIMIT_PUBLIC_PER_MINUTE` | integer | `120` | Max public endpoint requests per minute per IP. |

---

## 5. AI & Storage Configuration

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `AI_MODEL_PATH` | string | `"ai/model/priority_classifier.joblib"` | Path to serialized Scikit-Learn model artifact. |
| `STORAGE_LOCAL_DIR` | string | `"uploads/evidence"` | Local storage directory for uploaded evidence. |
| `MAX_UPLOAD_SIZE_MB` | integer | `10` | Maximum file upload size limit in megabytes. |
