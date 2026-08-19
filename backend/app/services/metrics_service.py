# Backward compatibility export
from app.core.metrics import metrics_collector, AppMetricsCollector

# Legacy class alias
MetricsCollector = AppMetricsCollector

__all__ = ["metrics_collector", "MetricsCollector", "AppMetricsCollector"]
