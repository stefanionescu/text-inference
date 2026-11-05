"""Public telemetry API — re-exports for convenience."""

from .sentry import capture_error, add_breadcrumb
from .traces import request_span, session_span, generation_span
from .lifecycle import shutdown_telemetry, initialize_telemetry
from .instruments import get_metrics, initialize_metrics

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
