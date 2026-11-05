"""Unit tests for telemetry error type mapping."""

from __future__ import annotations

from src.errors import RateLimitError, ValidationError, StreamCancelledError
from src.telemetry.error_classification import classify_error


def test_error_known_categories() -> None:
    """Test get error type known categories."""
    assert classify_error(ValidationError("invalid_payload", "bad payload")) == "validation"
    assert classify_error(RateLimitError(retry_after_seconds=1.0, limit=10, window_seconds=1.0)) == "rate_limit"
    assert classify_error(StreamCancelledError()) == "cancelled"
    assert classify_error(TimeoutError("deadline exceeded")) == "timeout"
    assert classify_error(ConnectionError("socket closed")) == "connection"


def test_error_unknown_category() -> None:
    """Test unclassified exceptions use the unknown telemetry category."""
    assert classify_error(RuntimeError("boom")) == "unknown"
