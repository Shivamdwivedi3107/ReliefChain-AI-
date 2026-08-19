# ReliefChain AI — Provider-Neutral Cloud Deployment Architecture

This guide outlines cloud deployment options for **ReliefChain AI** ranging from free student tiers to small production and auto-scaling cloud deployments.

---

## 1. Provider-Neutral Architecture Diagram

```
                              ┌────────────────────────────────┐
                              │    Public Client / PWA / Mobile │
                              └───────────────┬────────────────┘
                                              │ HTTPS (Port 443)
                                              ▼
                              ┌────────────────────────────────┐
                              │  Nginx Reverse Proxy / Ingress  │
                              │  - SSL Termination (Let's Encrypt)
                              │  - Gzip / Cache Header Management
                              │  - WebSocket Connection Upgrades│
                              └───────────────┬────────────────┘
                                              │
                      ┌───────────────────────┴───────────────────────┐
                      │ HTTP (Port 8000)                              │ WebSockets (`/ws`)
                      ▼                                               ▼
      ┌──────────────────────────────┐                ┌──────────────────────────────┐
      │ FastAPI Application Worker 1 │                │ FastAPI Application Worker 2 │
      └───────────────┬──────────────┘                └───────────────┬──────────────┘
                      │                                               │
                      └───────────────────────┬───────────────────────┘
                                              │ SQL (Psycopg2)
                                              ▼
                              ┌────────────────────────────────┐
                              │ PostgreSQL 16 Relational DB    │
                              │ - Docker Persistent Volume     │
                              │ - Daily Automated Checksum Dump│
                              └────────────────────────────────┘
```

---

## 2. Deployment Options & Cost Profiles

### Option A: Free / Low-Cost Student & Hackathon Tier
- **Compute**: Render, Railway, or Fly.io (Free Tier web service container).
- **Database**: Managed PostgreSQL (Supabase / Render Free Postgres) or SQLite persistent volume.
- **Cost**: **$0 / month**.
- **Configuration**:
  ```env
  ENVIRONMENT=staging
  DEBUG=False
  SECRET_KEY=<generate-random-32-char-key>
  DATABASE_URL=postgresql://user:pass@ep-free-db.provider.com/reliefchain
  BACKEND_CORS_ORIGINS=https://reliefchain-demo.onrender.com
  ```

### Option B: Small Production Deployment (Single Cloud VM)
- **Host**: AWS EC2 t3.small, GCP Compute Engine e2-small, or DigitalOcean $12/mo Droplet.
- **Runtime**: Docker Compose v2 with Nginx, FastAPI, and PostgreSQL 16 containers.
- **Cost**: **~$10--$20 / month**.
- **Commands**:
  ```bash
  git clone https://github.com/your-org/reliefchain-ai.git
  cd reliefchain-ai
  cp .env.example .env
  # Edit .env with production passwords and domain
  docker-compose -f docker-compose.prod.yml up -d --build
  ```

### Option C: High-Availability Scalable Production (Kubernetes / Managed Cloud)
- **Services**: AWS ECS / EKS, GCP Cloud Run / GKE.
- **Database**: AWS RDS PostgreSQL 16 Multi-AZ / GCP Cloud SQL.
- **Cache**: Managed Redis cluster for WebSocket pub-sub and sliding window rate-limiting.
- **Cost**: Scalable based on traffic demand.
