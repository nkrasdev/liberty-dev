from typing import Dict, Any
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest


# Global metrics registry
_metrics_registry = CollectorRegistry()

# Define metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status'],
    registry=_metrics_registry
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint'],
    registry=_metrics_registry
)

PRODUCT_OPERATIONS = Counter(
    'product_operations_total',
    'Total product operations',
    ['operation', 'source'],
    registry=_metrics_registry
)

SCRAPER_OPERATIONS = Counter(
    'scraper_operations_total',
    'Total scraper operations',
    ['source', 'status'],
    registry=_metrics_registry
)

ACTIVE_CONNECTIONS = Gauge(
    'active_connections',
    'Number of active connections',
    ['service'],
    registry=_metrics_registry
)


def setup_metrics() -> None:
    """Setup Prometheus metrics."""
    # Metrics are already defined globally
    pass


def get_metrics() -> str:
    """Get metrics in Prometheus format."""
    return generate_latest(_metrics_registry).decode('utf-8')


def get_metrics_dict() -> Dict[str, Any]:
    """Get metrics as a dictionary for debugging."""
    return {
        'request_count': REQUEST_COUNT._value.sum(),
        'request_duration': REQUEST_DURATION._sum.sum(),
        'product_operations': PRODUCT_OPERATIONS._value.sum(),
        'scraper_operations': SCRAPER_OPERATIONS._value.sum(),
        'active_connections': ACTIVE_CONNECTIONS._value.sum(),
    }
