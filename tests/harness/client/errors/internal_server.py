"""Internal server error type."""

from __future__ import annotations

from .server import ServerError, _register_error_code


@_register_error_code("internal_error")
class InternalServerError(ServerError):
    """Raised when an unexpected server error occurs."""

    user_message = "An unexpected server error occurred. Please try again."


__all__ = ["InternalServerError"]
