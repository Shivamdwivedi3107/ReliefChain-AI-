# ReliefChain AI — Operational Troubleshooting & Diagnostics Guide

## 1. Common Issues & Quick Resolutions

### Issue 1: `ModuleNotFoundError: No module named 'app'` when running Uvicorn
- **Symptom**: Starting Uvicorn from the workspace root results in an import error.
- **Resolution**: Use the root-level invocation:
  ```bash
  py -3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
  ```
  *(The `backend/app/main.py` script automatically injects `backend/` into `sys.path` on startup).*

---

### Issue 2: `OperationalError: no such column` on older SQLite databases
- **Symptom**: Upgrading from an older database version throws missing column errors on startup.
- **Resolution**: Automatic non-destructive schema sync is embedded in `backend/app/seed.py`. To trigger manually:
  ```bash
  py -3 backend/app/seed.py
  ```

---

### Issue 3: Port 8000 Already in Use
- **Symptom**: `OSError: [Errno 10048] error while attempting to bind on address ('127.0.0.1', 8000)`.
- **Resolution**:
  - Kill the existing process on Windows:
    ```powershell
    Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
    ```
  - Or bind to a different port:
    ```bash
    py -3 -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8080
    ```

---

### Issue 4: Docker Database Connection Timeout
- **Symptom**: Backend container fails healthcheck waiting for PostgreSQL.
- **Resolution**: Ensure the PostgreSQL container is fully healthy before backend starts. Docker Compose includes `depends_on: db: condition: service_healthy` to manage startup sequencing.

---

## 2. Health & Telemetry Verification
Check live subsystem readiness directly via HTTP:
```bash
# Check process liveness
curl http://127.0.0.1:8000/health/live

# Check deep system readiness (DB, AI Model, Ledger)
curl http://127.0.0.1:8000/health/ready

# Check Prometheus metrics
curl http://127.0.0.1:8000/metrics
```
