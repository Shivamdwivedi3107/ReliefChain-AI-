import sys
import time
import os
import uuid
from pathlib import Path
from contextlib import asynccontextmanager

# Ensure backend directory is in Python path for root-level execution
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import logger, request_id_ctx_var
from app.core.exceptions import (
    ReliefChainException,
    reliefchain_exception_handler,
    http_exception_handler,
    unhandled_exception_handler,
)
from app.routes import api_router, ws_router, metrics_router
from app.routes.health import router as health_root_router
from app.database import check_db_connection, Base, engine
from app.seed import seed_database
from app.services.metrics_service import metrics_collector


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup tasks
    logger.info(f"=== Starting {settings.PROJECT_NAME} ===")
    logger.info(f"Environment: {settings.ENVIRONMENT} | Debug: {settings.DEBUG}")
    try:
        Base.metadata.create_all(bind=engine)
        seed_database()
    except Exception as e:
        logger.warning(f"Auto-migration/seed note: {e}")
    db_status = check_db_connection()
    logger.info(f"Database Connectivity Check: {'SUCCESS' if db_status else 'ATTENTION NEEDED'}")
    yield
    # Shutdown tasks
    logger.info(f"=== Shutting down {settings.PROJECT_NAME} ===")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description=(
        "Blockchain-Powered Disaster Relief, Resource Tracking, "
        "and AI-Based Emergency Prioritization Platform Backend."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

from fastapi.middleware.trustedhost import TrustedHostMiddleware

# Trusted Host Middleware (when allowed hosts configured without wildcard)
allowed_hosts = settings.ALLOWED_HOSTS if isinstance(settings.ALLOWED_HOSTS, list) else [settings.ALLOWED_HOSTS]
if allowed_hosts and "*" not in allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=allowed_hosts)

# CORS Configuration
origins = (
    settings.BACKEND_CORS_ORIGINS
    if isinstance(settings.BACKEND_CORS_ORIGINS, list)
    else [settings.BACKEND_CORS_ORIGINS]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request Correlation ID, Performance Timing & Telemetry Middleware
@app.middleware("http")
async def correlation_and_timing_middleware(request: Request, call_next):
    req_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = req_id
    token = request_id_ctx_var.set(req_id)

    metrics_collector.start_request()
    start_time = time.time()
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000

        # Record metrics telemetry
        metrics_collector.end_request(
            endpoint=request.url.path,
            status_code=response.status_code,
            duration_ms=process_time,
        )

        # Security Headers
        response.headers["X-Request-ID"] = req_id
        response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        logger.info(
            f"{request.method} {request.url.path} -> Status {response.status_code} ({process_time:.2f}ms)"
        )
        return response
    finally:
        request_id_ctx_var.reset(token)


# Centralized Exception Handlers
app.add_exception_handler(ReliefChainException, reliefchain_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    req_id = getattr(request.state, "request_id", request_id_ctx_var.get())
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request payload validation failed.",
                "details": exc.errors(),
                "request_id": req_id,
                "path": request.url.path,
            },
        },
    )


app.add_exception_handler(Exception, unhandled_exception_handler)


# Root Endpoint
@app.get("/", tags=["Root"])
def root_endpoint():
    return {
        "project": settings.PROJECT_NAME,
        "version": "2.0.0",
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
        "health": "/health",
        "health_v1": f"{settings.API_V1_STR}/health",
        "metrics": "/metrics",
    }


# Include Root Health Probes
app.include_router(health_root_router)

# Include Telemetry Metrics Endpoint
app.include_router(metrics_router)

# Include WebSockets
app.include_router(ws_router)

# Include API v1 Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Uploads directory static mount
uploads_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
if not os.path.exists(uploads_dir):
    os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")

# Frontend Static Files Mount
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="frontend")
