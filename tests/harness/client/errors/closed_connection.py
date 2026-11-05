"""Closed WebSocket connection error type."""

from __future__ import annotations

from .websocket_connection import WebSocketConnectionError


class ConnectionClosedError(WebSocketConnectionError):
    """Raised when the WebSocket connection closes unexpectedly."""

    def __init__(
        self,
        message: str = "WebSocket connection closed",
        *,
        close_code: int | None = None,
        close_reason: str | None = None,
    ) -> None:
        """Build a connection-closed error with optional close metadata.

        Args:
            message: Message to send, check, or report.
            close_code: Code of the close.
            close_reason: Close reason.

        """
        self.close_code = close_code
        self.close_reason = close_reason
        parts = [message]
        if close_code is not None:
            parts.append(f"code={close_code}")
        if close_reason:
            parts.append(f"reason={close_reason}")
        super().__init__(" ".join(parts))


__all__ = ["ConnectionClosedError"]
