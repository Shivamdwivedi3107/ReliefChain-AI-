import time
import threading
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status
from app.core.config import settings
from app.core.logging import logger
from app.core.metrics import metrics_collector


class InMemoryRateLimiter:
    """
    Lightweight, thread-safe in-memory sliding window rate limiter.
    Does not require external Redis dependency.
    """
    def __init__(self):
        self._lock = threading.Lock()
        # Key: (ip/key, route) -> list of timestamp floats
        self._records: Dict[str, List[float]] = defaultdict(list)

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> Tuple[bool, int]:
        """
        Check if request is allowed under rate limit.
        Returns: (is_allowed: bool, retry_after_seconds: int)
        """
        if not settings.RATE_LIMIT_ENABLED:
            return True, 0

        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            timestamps = self._records[key]
            # Prune old timestamps outside window
            valid_timestamps = [ts for ts in timestamps if ts > window_start]
            self._records[key] = valid_timestamps

            if len(valid_timestamps) >= max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(earliest + window_seconds - now))
                return False, retry_after

            self._records[key].append(now)
            return True, 0


rate_limiter = InMemoryRateLimiter()


def rate_limit_dependency(max_requests: int = 15, window_seconds: int = 60):
    """FastAPI Dependency for per-IP rate limiting with telemetry integration."""
    def dependency(request: Request):
        if not settings.RATE_LIMIT_ENABLED:
            return

        client_ip = request.client.host if request.client else "unknown"
        endpoint = request.url.path
        key = f"{client_ip}:{endpoint}"

        allowed, retry_after = rate_limiter.is_allowed(
            key=key,
            max_requests=max_requests,
            window_seconds=window_seconds,
        )

        if not allowed:
            metrics_collector.record_rate_limit_rejection()
            logger.warning(f"Rate limit exceeded for IP {client_ip} on {endpoint}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)},
            )

    return dependency


def get_rate_limit_for_role(role: str | None = None) -> int:
    """Return rate limit quota per minute based on client authentication status/role."""
    if not role or role == "public":
        return settings.RATE_LIMIT_PUBLIC_PER_MINUTE
    return settings.RATE_LIMIT_AUTH_PER_MINUTE

