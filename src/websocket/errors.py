"""Shared response helpers for WebSocket error handling.

This module provides standardized error response formatting for WebSocket
connections. All error responses use the flat format:

    {"type": "error", "status": N, "code": "...", "message": "..."}
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from config.runtime.websocket import ERROR_CODE_TO_STATUS, WEBSOCKET_STATUS_INTERNAL

from .transport import safe_send_flat

if TYPE_CHECKING:
    from fastapi import WebSocket


async def send_error(
    websocket: WebSocket,
    *,
    status: int | None = None,
    code: str,
    message: str,
) -> None:
    """Send a structured error message to the client.

    If status is not provided, it is looked up from ERROR_CODE_TO_STATUS
    using the code. Falls back to 500 if not found.

    Args:
        websocket: WebSocket connection of the client.
        status: Status code to report.
        code: Error or close code.
        message: Message to send, check, or report.

    """
    resolved_status = status if status is not None else ERROR_CODE_TO_STATUS.get(code, WEBSOCKET_STATUS_INTERNAL)
    await safe_send_flat(websocket, "error", status=resolved_status, code=code, message=message)


async def reject_connection(
    websocket: WebSocket,
    *,
    code: str,
    message: str,
    close_code: int,
) -> None:
    """Accept connection briefly to send an error, then close immediately.

    Args:
        websocket: WebSocket connection of the client.
        code: Error or close code.
        message: Message to send, check, or report.
        close_code: Code of the close.

    """
    await websocket.accept()
    await send_error(websocket, code=code, message=message)
    await websocket.close(code=close_code)


__all__ = ["reject_connection", "send_error"]
