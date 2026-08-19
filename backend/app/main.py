import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.logging import logger
from app.routes import api_router
from app.database import check_db_connection, Base, engine
from app.seed import seed_database


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
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

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


# Request timing & Logging Middleware
@app.middleware("http")
async def log_requests_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = (time.time() - start_time) * 1000
    logger.info(
        f"{request.method} {request.url.path} -> Status {response.status_code} ({process_time:.2f}ms)"
    )
    response.headers["X-Process-Time-Ms"] = f"{process_time:.2f}"
    return response


# Centralized Exception Handlers
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning(f"HTTP {exc.status_code} on {request.url.path}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": exc.detail,
            "path": request.url.path,
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
            "message": "Request validation failed",
            "errors": exc.errors(),
            "path": request.url.path,
        },
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled server error on {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "An internal server error occurred.",
            "path": request.url.path,
        },
    )


# Root Endpoint
@app.get("/", tags=["Root"])
def root_endpoint():
    return {
        "project": settings.PROJECT_NAME,
        "status": "online",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR,
        "health": f"{settings.API_V1_STR}/health",
    }


# Include API Routers
app.include_router(api_router, prefix=settings.API_V1_STR)

# Optional Static Files Mount for Frontend
import os
from fastapi.staticfiles import StaticFiles
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_path):
    app.mount("/ui", StaticFiles(directory=frontend_path, html=True), name="frontend")
