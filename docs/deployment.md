# ReliefChain AI — Production Deployment Guide

This document outlines the step-by-step procedures for deploying ReliefChain AI across containerized environments (Docker / Docker Compose), reverse proxy frontends (Nginx), and cloud orchestrators (Kubernetes / ECS).

---

## 1. Prerequisites & System Requirements

- **Runtime Engine**: Docker Engine 24.0+ & Docker Compose v2.20+
- **Host System**: Linux (Ubuntu 22.04 LTS recommended) or Windows Server
- **Minimum Compute**: 2 vCPU, 4GB RAM, 20GB SSD Storage
- **Network Access**: Inbound TCP ports 80 (HTTP), 443 (HTTPS)
- **Domain & DNS**: Valid A/AAAA records pointing to host IP

---

## 2. Quick Deploy with Docker Compose (Production 3-Tier)

ReliefChain AI ships with a production-optimized 3-tier architecture:
- **Tier 1**: Nginx Edge Reverse Proxy (`proxy`)
- **Tier 2**: FastAPI Application Backend with ASGI worker pooling (`backend`)
- **Tier 3**: PostgreSQL 16 Alpine Relational Database (`db`) on an isolated private network

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/reliefchain/reliefchain-ai.git
cd reliefchain-ai

# Create production .env configuration
cp .env.example .env
```

Generate a secure 64-character secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Update `.env` with production variables:
```dotenv
ENVIRONMENT=production
DEBUG=False
SECRET_KEY="<your-generated-64-character-token>"
DOMAIN_NAME="api.reliefchain.org"
ALLOWED_HOSTS="api.reliefchain.org,localhost"
POSTGRES_USER=reliefchain
POSTGRES_PASSWORD="<strong-database-password>"
POSTGRES_DB=reliefchain
BACKEND_CORS_ORIGINS="https://reliefchain.org,https://api.reliefchain.org"
LOG_LEVEL=INFO
LOG_FORMAT=json
WORKERS=4
```

### Step 2: Build & Start Production Stack
```bash
docker compose -f docker-compose.prod.yml up -d --build
```

### Step 3: Verify Service Health
```bash
# Check running containers
docker compose -f docker-compose.prod.yml ps

# Check deep readiness probe
curl -f http://localhost/health/ready
```

---

## 3. Kubernetes Deployment Blueprint

For Kubernetes deployments, ReliefChain AI can be provisioned using standard StatefulSets and Deployments:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: reliefchain-backend
  namespace: reliefchain
spec:
  replicas: 3
  selector:
    matchLabels:
      app: reliefchain-backend
  template:
    metadata:
      labels:
        app: reliefchain-backend
    spec:
      containers:
        - name: backend
          image: reliefchain/backend:2.0.0
          imagePullPolicy: IfNotPresent
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: reliefchain-config
            - secretRef:
                name: reliefchain-secrets
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 15
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 15
            periodSeconds: 20
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1024Mi"
```

---

## 4. Reverse Proxy & SSL/TLS Termination

In production, TLS termination is handled at the Nginx edge:

1. Obtain SSL certificates via Certbot / Let's Encrypt:
```bash
sudo certbot certonly --standalone -d api.reliefchain.org
```

2. Mount certificates in `docker-compose.prod.yml`:
```yaml
volumes:
  - /etc/letsencrypt/live/api.reliefchain.org/fullchain.pem:/etc/nginx/ssl/fullchain.pem:ro
  - /etc/letsencrypt/live/api.reliefchain.org/privkey.pem:/etc/nginx/ssl/privkey.pem:ro
```

3. Enable the HTTPS server block in `nginx/conf.d/default.conf`.

---

## 5. Rollbacks & Blue/Green Zero-Downtime Updates

```bash
# Pull updated image
docker pull reliefchain/backend:latest

# Rolling update backend container
docker compose -f docker-compose.prod.yml up -d --no-deps --build backend
```
