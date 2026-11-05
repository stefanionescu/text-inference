"""Server capacity limit error."""

from __future__ import annotations

from .server import ServerError, _register_error_code


@_register_error_code("server_at_capacity")
class ServerAtCapacityError(ServerError):
    """Raised when the server is at maximum connection capacity.

    Attributes:
        user_message: User message.

    """

    _is_recoverable = True
    user_message = "Server is busy. Please try again later."


__all__ = ["ServerAtCapacityError"]
