"""Stream error type."""

from __future__ import annotations

from .client import TestClientError


class StreamError(TestClientError):
    """Raised when stream consumption encounters a server error."""

    def __init__(self, message: dict[str, object]) -> None:
        """Initialize the error with the server message payload."""
        self.message = message
        super().__init__(str(message))


__all__ = ["StreamError"]
