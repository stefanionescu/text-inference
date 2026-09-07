"""Idle timeout error type."""

from __future__ import annotations

from .closed_connection import ConnectionClosedError
from config.tests.defaults import WEBSOCKET_IDLE_CLOSE_CODE, WEBSOCKET_IDLE_CLOSE_REASON


class IdleTimeoutError(ConnectionClosedError):
    """Raised when the server closes the connection due to inactivity."""

    def __init__(
        self,
        message: str = "Connection closed due to inactivity",
        *,
        close_code: int | None = WEBSOCKET_IDLE_CLOSE_CODE,
        close_reason: str | None = WEBSOCKET_IDLE_CLOSE_REASON,
    ) -> None:
        """Build an idle-timeout close error."""
        super().__init__(message, close_code=close_code, close_reason=close_reason)

    @staticmethod
    def matches(close_code: int | None, close_reason: str | None) -> bool:
        """Return whether close metadata represents an idle timeout."""
        if close_code == WEBSOCKET_IDLE_CLOSE_CODE:
            return True
        if close_reason is None:
            return False
        return "idle" in close_reason.lower()


__all__ = ["IdleTimeoutError"]
