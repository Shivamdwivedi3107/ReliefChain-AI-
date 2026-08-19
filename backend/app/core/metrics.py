import time
import threading
from collections import defaultdict
from typing import Dict, Any, Optional


class AppMetricsCollector:
    """
    Thread-safe production observability metrics collector.
    Tracks HTTP traffic, latency distributions, operational events, and system errors.
    """

    def __init__(self):
        self._lock = threading.Lock()
        self.start_time = time.time()
        
        # Traffic & HTTP metrics
        self.http_requests_total = 0
        self.http_errors_total = 0
        self.active_requests = 0
        self.requests_by_endpoint: Dict[str, int] = defaultdict(int)
        self.requests_by_status: Dict[int, int] = defaultdict(int)
        self.total_duration_ms: float = 0.0

        # Security & Authentication metrics
        self.auth_failures_total = 0
        self.rate_limit_rejections_total = 0

        # Domain operational counters
        self.relief_requests_created_total = 0
        self.missions_completed_total = 0
        self.qr_verifications_total = 0
        self.ai_prediction_requests_total = 0

    def start_request(self):
        with self._lock:
            self.active_requests += 1

    def end_request(self, endpoint: str, status_code: int, duration_ms: float = 0.0):
        with self._lock:
            self.active_requests = max(0, self.active_requests - 1)
            self.http_requests_total += 1
            self.total_duration_ms += duration_ms
            if status_code >= 400:
                self.http_errors_total += 1
            self.requests_by_endpoint[endpoint] += 1
            self.requests_by_status[status_code] += 1

    def record_request(self, endpoint: str, status_code: int, duration_ms: float = 0.0):
        """Backward-compatible alias for recording HTTP request metrics."""
        self.end_request(endpoint=endpoint, status_code=status_code, duration_ms=duration_ms)

    def record_auth_failure(self):
        with self._lock:
            self.auth_failures_total += 1

    def record_rate_limit_rejection(self):
        with self._lock:
            self.rate_limit_rejections_total += 1

    def record_ai_prediction(self):
        with self._lock:
            self.ai_prediction_requests_total += 1

    def record_qr_verification(self):
        with self._lock:
            self.qr_verifications_total += 1

    def record_relief_request_created(self):
        with self._lock:
            self.relief_requests_created_total += 1

    def record_mission_completed(self):
        with self._lock:
            self.missions_completed_total += 1

    def get_metrics_summary(self, db_stats: Optional[Dict[str, int]] = None, active_ws_count: int = 0) -> Dict[str, Any]:
        uptime = round(time.time() - self.start_time, 2)
        with self._lock:
            avg_latency = round(self.total_duration_ms / max(1, self.http_requests_total), 2)
            return {
                "uptime_seconds": uptime,
                "active_requests": self.active_requests,
                "http_requests_total": self.http_requests_total,
                "http_errors_total": self.http_errors_total,
                "average_latency_ms": avg_latency,
                "auth_failures_total": self.auth_failures_total,
                "rate_limit_rejections_total": self.rate_limit_rejections_total,
                "ai_prediction_requests_total": self.ai_prediction_requests_total,
                "qr_verifications_total": self.qr_verifications_total,
                "active_websocket_connections": active_ws_count,
                "requests_by_status": dict(self.requests_by_status),
                "database_entities": db_stats or {},
            }

    def generate_prometheus_text(self, db_stats: Optional[Dict[str, int]] = None, active_ws_count: int = 0) -> str:
        uptime = round(time.time() - self.start_time, 2)
        with self._lock:
            avg_latency = round(self.total_duration_ms / max(1, self.http_requests_total), 2)
            stats = db_stats or {}
            lines = [
                "# HELP reliefchain_uptime_seconds Total runtime of ReliefChain AI backend in seconds",
                "# TYPE reliefchain_uptime_seconds gauge",
                f"reliefchain_uptime_seconds {uptime}",
                "",
                "# HELP reliefchain_http_requests_total Total number of HTTP requests handled",
                "# TYPE reliefchain_http_requests_total counter",
                f"reliefchain_http_requests_total {self.http_requests_total}",
                "",
                "# HELP reliefchain_http_errors_total Total number of HTTP 4xx/5xx errors",
                "# TYPE reliefchain_http_errors_total counter",
                f"reliefchain_http_errors_total {self.http_errors_total}",
                "",
                "# HELP reliefchain_active_requests Current in-flight HTTP requests being processed",
                "# TYPE reliefchain_active_requests gauge",
                f"reliefchain_active_requests {self.active_requests}",
                "",
                "# HELP reliefchain_average_latency_ms Average HTTP request process latency in milliseconds",
                "# TYPE reliefchain_average_latency_ms gauge",
                f"reliefchain_average_latency_ms {avg_latency}",
                "",
                "# HELP reliefchain_auth_failures_total Total failed authentication attempts",
                "# TYPE reliefchain_auth_failures_total counter",
                f"reliefchain_auth_failures_total {self.auth_failures_total}",
                "",
                "# HELP reliefchain_rate_limit_rejections_total Total requests throttled by rate limiter",
                "# TYPE reliefchain_rate_limit_rejections_total counter",
                f"reliefchain_rate_limit_rejections_total {self.rate_limit_rejections_total}",
                "",
                "# HELP reliefchain_ai_prediction_requests_total Total AI emergency triage predictions evaluated",
                "# TYPE reliefchain_ai_prediction_requests_total counter",
                f"reliefchain_ai_prediction_requests_total {self.ai_prediction_requests_total}",
                "",
                "# HELP reliefchain_active_websockets Current open real-time WebSocket subscriber connections",
                "# TYPE reliefchain_active_websockets gauge",
                f"reliefchain_active_websockets {active_ws_count}",
                "",
                "# HELP reliefchain_relief_requests_total Total registered disaster SOS relief requests in DB",
                "# TYPE reliefchain_relief_requests_total gauge",
                f"reliefchain_relief_requests_total {stats.get('relief_requests', 0)}",
                "",
                "# HELP reliefchain_missions_completed_total Total delivered and completed missions in DB",
                "# TYPE reliefchain_missions_completed_total gauge",
                f"reliefchain_missions_completed_total {stats.get('completed_missions', 0)}",
                "",
                "# HELP reliefchain_qr_verifications_total Total verified single-use delivery handovers in DB",
                "# TYPE reliefchain_qr_verifications_total gauge",
                f"reliefchain_qr_verifications_total {stats.get('qr_verifications', 0)}",
                "",
                "# HELP reliefchain_donations_total Total humanitarian funding and aid sponsorships in DB",
                "# TYPE reliefchain_donations_total gauge",
                f"reliefchain_donations_total {stats.get('donations', 0)}",
            ]
            return "\n".join(lines) + "\n"


metrics_collector = AppMetricsCollector()
