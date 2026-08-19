# ReliefChain AI — Production Deployment Guide

## 1. Prerequisites & System Requirements
- **Docker & Docker Compose** (v24.0+ / Compose v2.20+)
- **Python 3.11+** (for bare-metal execution)
- **PostgreSQL 16** (or SQLite for development)
- **RAM**: Minimum 2GB (4GB recommended)
- **Disk**: 10GB free space

---

## 2. Option A: Production Multi-Container Docker Deployment

### Step 1: Clone and Configure Environment
```bash
git clone https://github.com/your-org/reliefchain-ai.git
cd reliefchain-ai

# Copy environment template
cp .env.example .env

# Generate secure 32+ character secrets
# python -c "import secrets; print(secrets.token_hex(32))"
```

Edit `.env` to configure:
```env
ENVIRONMENT=production
DEBUG=False
SECRET_KEY=your_production_secure_secret_key_at_least_32_chars_long!
POSTGRES_USER=reliefchain
POSTGRES_PASSWORD=your_secure_db_password
POSTGRES_DB=reliefchain
DATABASE_URL=postgresql+psycopg2://reliefchain:your_secure_db_password@db:5432/reliefchain
BACKEND_CORS_ORIGINS=https://reliefchain.yourdomain.org,http://localhost:8000
```

### Step 2: Build & Start Stack
```bash
docker-compose -f docker-compose.prod.yml up -d --build
```

### Step 3: Run Database Migrations & Seed Baseline Catalogs
```bash
docker-compose -f docker-compose.prod.yml exec backend python -m alembic upgrade head
docker-compose -f docker-compose.prod.yml exec backend python backend/app/seed.py
```

---

## 3. Option B: Local Bare-Metal Execution (Development)

From repository root:
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start backend and web application on port 8000
py -3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

Access in your browser:
- 🌐 **Web App & PWA**: [http://127.0.0.1:8000/ui/](http://127.0.0.1:8000/ui/)
- 📖 **Interactive Swagger Docs**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- 📊 **Prometheus Metrics**: [http://127.0.0.1:8000/metrics](http://127.0.0.1:8000/metrics)
- 🩺 **Health Readiness**: [http://127.0.0.1:8000/health/ready](http://127.0.0.1:8000/health/ready)

---

## 4. Nginx Reverse Proxy Configuration & SSL
The `nginx/nginx.conf` handles SSL termination, gzip compression, and WebSocket upgrade proxying:
```nginx
location /ws {
    proxy_pass http://backend:8000/ws;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "Upgrade";
    proxy_set_header Host $host;
}
```
