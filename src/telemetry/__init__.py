"""Public telemetry API — re-exports for convenience."""

from .sentry import add_breadcrumb, capture_error
from .instruments import get_metrics, initialize_metrics
from .lifecycle import initialize_telemetry, shutdown_telemetry
from .traces import generation_span, request_span, session_span

__all__ = [
    "add_breadcrumb",
    "capture_error",
    "generation_span",
    "get_metrics",
    "initialize_metrics",
    "initialize_telemetry",
    "request_span",
    "session_span",
    "shutdown_telemetry",
]
