"""Rejected WebSocket connection error type."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .websocket_connection import WebSocketConnectionError

if TYPE_CHECKING:
    from .server import ServerError


class ConnectionRejectedError(WebSocketConnectionError):
    """Raised when the server rejects a connection attempt."""

    def __init__(self, server_error: ServerError) -> None:
        """Build a rejection error from a parsed server error.

        Args:
            server_error: Server error.

        """
        self.server_error = server_error
        super().__init__(f"Connection rejected: {server_error}")


__all__ = ["ConnectionRejectedError"]
