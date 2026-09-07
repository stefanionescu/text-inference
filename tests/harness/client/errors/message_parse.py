"""Message parse error type."""

from __future__ import annotations

from .client import TestClientError


class MessageParseError(TestClientError):
    """Raised when a WebSocket frame cannot be parsed into JSON."""


__all__ = ["MessageParseError"]
