"""Send flat WebSocket frames with disconnect handling and latency metrics."""

from __future__ import annotations

import json
import time
import logging

from fastapi import WebSocket, WebSocketDisconnect

from src.telemetry.instruments import get_metrics

logger = logging.getLogger(__name__)


def build_flat_message(message_type: str, *, status: int | None = None, **fields: object) -> dict[str, object]:
    """Build a flat WebSocket message dict."""
    message: dict[str, object] = {"type": message_type}
    if status is not None:
        message["status"] = status
    message.update({key: value for key, value in fields.items() if value is not None})
    return message


async def safe_send_text(websocket: WebSocket, text: str) -> bool:
    """Send text to the client, returning False if the socket is gone."""
    try:
        await websocket.send_text(text)
    except WebSocketDisconnect:
        metrics = get_metrics()
        metrics.disconnect_mid_stream_total.add(1)
        metrics.phase_errors_total.add(1, {"phase": "send", "error.type": "client_disconnect"})
        logger.info("WebSocket disconnected while sending %s bytes", len(text))
        return False
    return True


async def safe_send_json(websocket: WebSocket, payload: dict[str, object]) -> bool:
    """Send a JSON payload, swallowing client disconnects."""
    started_at = time.perf_counter()
    sent = await safe_send_text(websocket, json.dumps(payload))
    elapsed = time.perf_counter() - started_at
    metrics = get_metrics()
    metrics.phase_latency.record(max(0.0, elapsed), {"phase": "send"})
    metrics.websocket_send_latency.record(elapsed)
    return sent


async def safe_send_flat(
    websocket: WebSocket, message_type: str, *, status: int | None = None, **fields: object
) -> bool:
    """Send a flat-format JSON message."""
    payload = build_flat_message(message_type, status=status, **fields)
    return await safe_send_json(websocket, payload)


__all__ = [
    "build_flat_message",
    "safe_send_flat",
    "safe_send_json",
    "safe_send_text",
]
