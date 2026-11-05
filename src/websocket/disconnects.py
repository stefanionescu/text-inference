"""Helpers for classifying expected WebSocket transport disconnects."""

from __future__ import annotations

from anyio import EndOfStream, BrokenResourceError, ClosedResourceError
from fastapi import WebSocketDisconnect
from websockets.exceptions import ConnectionClosed

WEBSOCKET_DISCONNECT_ERRORS: tuple[type[BaseException], ...] = (
    WebSocketDisconnect,
    ConnectionClosed,
    ConnectionResetError,
    BrokenPipeError,
    EOFError,
    BrokenResourceError,
    ClosedResourceError,
    EndOfStream,
)


def is_expected_websocket_disconnect(exception: BaseException) -> bool:
    """Return True when exception indicates expected transport disconnect.

    Args:
        exception: Exception to inspect.

    Returns:
        True when exception indicates expected transport disconnect.

    """
    return isinstance(exception, WEBSOCKET_DISCONNECT_ERRORS)


__all__ = [
    "WEBSOCKET_DISCONNECT_ERRORS",
    "is_expected_websocket_disconnect",
]
