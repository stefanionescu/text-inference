"""Map exceptions to telemetry error-type labels."""

from __future__ import annotations

from src.errors import RateLimitError, ValidationError, StreamCancelledError

ERROR_TYPE_LABELS: tuple[tuple[type[BaseException], str], ...] = (
    (ValidationError, "validation"),
    (RateLimitError, "rate_limit"),
    (StreamCancelledError, "cancelled"),
    (TimeoutError, "timeout"),
    (ConnectionError, "connection"),
)


def classify_error(exception: BaseException) -> str:
    """Return the telemetry error type label for an exception."""
    for exception_type, label in ERROR_TYPE_LABELS:
        if isinstance(exception, exception_type):
            return label
    return "unknown"


__all__ = ["classify_error"]
