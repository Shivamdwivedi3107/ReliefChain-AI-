import traceback
from typing import Optional, Any, Dict
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger, request_id_ctx_var


class ReliefChainException(Exception):
    def __init__(self, code: str, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class ResourceNotFoundError(ReliefChainException):
    def __init__(self, resource_type: str, resource_id: str):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource_type} with ID '{resource_id}' was not found.",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class PermissionDeniedError(ReliefChainException):
    def __init__(self, message: str = "Permission denied for this operation."):
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class InvalidStatusTransitionError(ReliefChainException):
    def __init__(self, current_status: str, target_status: str, allowed: list):
        super().__init__(
            code="INVALID_STATUS_TRANSITION",
            message=f"Cannot transition mission from '{current_status}' to '{target_status}'. Allowed transitions: {allowed}",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"current_status": current_status, "target_status": target_status, "allowed": allowed},
        )


class InventoryUnavailableError(ReliefChainException):
    def __init__(self, resource_name: str, requested: float, available: float):
        super().__init__(
            code="INSUFFICIENT_INVENTORY",
            message=f"Cannot allocate {requested} units of '{resource_name}'. Only {available} available in depot.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"requested": requested, "available": available},
        )


class QRAlreadyRedeemedError(ReliefChainException):
    def __init__(self, qr_token: str):
        super().__init__(
            code="QR_ALREADY_REDEEMED",
            message="This cryptographic QR delivery token has already been verified and cannot be reused.",
            status_code=status.HTTP_400_BAD_REQUEST,
            details={"token": qr_token},
        )


async def reliefchain_exception_handler(request: Request, exc: ReliefChainException):
    req_id = getattr(request.state, "request_id", request_id_ctx_var.get())
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": exc.message,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
                "request_id": req_id,
                "path": str(request.url.path),
            },
        },
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    req_id = getattr(request.state, "request_id", request_id_ctx_var.get())
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        422: "VALIDATION_ERROR",
        429: "RATE_LIMIT_EXCEEDED",
    }
    code = code_map.get(exc.status_code, "HTTP_ERROR")
    msg = exc.detail if isinstance(exc.detail, str) else str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        headers=exc.headers,
        content={
            "success": False,
            "status_code": exc.status_code,
            "message": msg,
            "error": {
                "code": code,
                "message": msg,
                "request_id": req_id,
                "path": str(request.url.path),
            },
        },
    )


async def unhandled_exception_handler(request: Request, exc: Exception):
    req_id = getattr(request.state, "request_id", request_id_ctx_var.get())
    logger.error(f"Unhandled exception on {request.method} {request.url.path}: {exc}\n{traceback.format_exc()}")
    
    error_payload = {
        "code": "INTERNAL_SERVER_ERROR",
        "message": "An unexpected server error occurred. Please contact system support.",
        "request_id": req_id,
        "path": str(request.url.path),
    }
    
    if settings.DEBUG and settings.ENVIRONMENT == "development":
        error_payload["debug_trace"] = str(exc)

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "message": "An unexpected server error occurred.",
            "error": error_payload,
        },
    )
