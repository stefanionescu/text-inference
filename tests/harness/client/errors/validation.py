"""Validation server error type."""

from __future__ import annotations

from .server import ServerError, _register_error_code


@_register_error_code("invalid_payload", "invalid_settings", "validation_error")
class ValidationError(ServerError):
    """Raised when the server rejects input due to validation failures."""


__all__ = ["ValidationError"]
