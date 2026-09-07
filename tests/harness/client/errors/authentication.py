"""Authentication server error type."""

from __future__ import annotations

from .server import ServerError, _register_error_code


@_register_error_code("authentication_failed")
class AuthenticationError(ServerError):
    """Raised when authentication fails (invalid or missing API key)."""

    user_message = "Authentication failed. Please check your API key (--api-key or API_KEY environment variable)."


__all__ = ["AuthenticationError"]
