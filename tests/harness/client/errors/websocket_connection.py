"""WebSocket connection base error type."""

from __future__ import annotations

from .client import TestClientError


class WebSocketConnectionError(TestClientError):
    """Base class for WebSocket connection issues."""


__all__ = ["WebSocketConnectionError"]
