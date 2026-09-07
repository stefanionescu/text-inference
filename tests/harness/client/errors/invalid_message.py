"""Invalid message server error type."""

from __future__ import annotations

from .server import ServerError, _register_error_code


@_register_error_code("invalid_message", "unknown_message_type")
class InvalidMessageError(ServerError):
    """Raised when the server receives a malformed or unknown message."""


__all__ = ["InvalidMessageError"]
