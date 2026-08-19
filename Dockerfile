# ==============================================================================
# ReliefChain AI - Production Dockerfile
# ==============================================================================

FROM python:3.11-slim as builder

WORKDIR /app

# Install system build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final runtime image
FROM python:3.11-slim as runner

WORKDIR /app

# Install runtime libpq for PostgreSQL connectivity and curl for healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user and group
RUN groupadd -r reliefchain && useradd -r -g reliefchain -m -d /home/reliefchain reliefchain

# Copy Python packages from builder
COPY --from=builder /root/.local /home/reliefchain/.local
ENV PATH=/home/reliefchain/.local/bin:$PATH
ENV PYTHONPATH=/app/backend:/app

# Copy application source code
COPY backend/ /app/backend/
COPY ai/ /app/ai/
COPY frontend/ /app/frontend/

# Set ownership to non-root user
RUN chown -R reliefchain:reliefchain /app

# Switch to non-root user
USER reliefchain

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    ENVIRONMENT=production \
    DEBUG=False \
    HOST=0.0.0.0 \
    PORT=8000

# Expose FastAPI port
EXPOSE 8000

# Container Healthcheck probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Workdir for application execution
WORKDIR /app/backend

# Start production ASGI server with configurable workers
CMD ["sh", "-c", "python -m uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers ${WORKERS:-4}"]
