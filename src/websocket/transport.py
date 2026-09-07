"""WebSocket streaming and communication utilities.

This module provides helper functions for safe WebSocket communication
and streaming model responses. It handles:

1. Safe Sending:
   - Catching WebSocketDisconnect during send operations
   - Returning boolean success indicators for flow control

2. Streaming Infrastructure:
   - Forwarding async streams to WebSocket clients
   - Sending token/final/done message frames
   - Recording conversation history on completion

Message Protocol:
    All messages use a flat format: {"type": "...", "status": N, ...fields}
"""

from __future__ import annotations

import json
import time
import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass
from src.telemetry.instruments import get_metrics
from fastapi import WebSocket, WebSocketDisconnect
from config.runtime.websocket import WEBSOCKET_STATUS_OK

if TYPE_CHECKING:
    from collections.abc import AsyncIterator
    from src.state.session import SessionState
    from src.session.runtime import SessionRuntime

logger = logging.getLogger(__name__)


@dataclass
class _StreamState:
    """Internal state for stream_response."""

    completion_text: str
    is_text_visible: bool
    is_interrupted: bool = False


@dataclass(frozen=True)
class StreamResponseRequest:
    """Inputs for streaming one model response to a websocket."""

    websocket: WebSocket
    stream: AsyncIterator[str]
    connection_state: SessionState
    user_utterance: str
    session_runtime: SessionRuntime
    initial_text: str = ""
    is_initial_text_sent: bool = True
    history_user_utterance: str | None = None


# ============================================================================
# Private helpers
# ============================================================================


async def _send_initial_text(
    websocket: WebSocket,
    initial_text: str,
    state: _StreamState,
    *,
    is_already_sent: bool,
) -> None:
    """Send initial text when it was not already emitted."""
    if not initial_text or is_already_sent:
        return
    sent = await safe_send_flat(websocket, "token", text=initial_text)
    if sent:
        state.is_text_visible = True
    else:
        state.is_interrupted = True


async def _forward_stream_chunks(
    websocket: WebSocket,
    stream: AsyncIterator[str],
    state: _StreamState,
) -> None:
    """Forward generated stream chunks to the client."""
    async for chunk in stream:
        sent = await safe_send_flat(websocket, "token", text=chunk)
        if not sent:
            state.is_interrupted = True
            break
        state.completion_text += chunk
        state.is_text_visible = True


async def _send_completion_frames(websocket: WebSocket, state: _StreamState) -> None:
    """Send final and done frames for a completed stream."""
    sent_completion = await safe_send_flat(websocket, "final", status=WEBSOCKET_STATUS_OK, text=state.completion_text)
    if not sent_completion:
        state.is_interrupted = True
        return
    sent_done = await safe_send_flat(websocket, "done", status=WEBSOCKET_STATUS_OK)
    if not sent_done:
        state.is_interrupted = True


async def _handle_empty_output(websocket: WebSocket) -> None:
    """Report an empty model output to metrics and client."""
    logger.warning("empty model output")
    get_metrics().empty_model_output_total.add(1)
    await safe_send_flat(
        websocket,
        "error",
        status=500,
        code="internal_error",
        message="Model produced no output",
    )


# ============================================================================
# Public API
# ============================================================================


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


async def stream_response(request: StreamResponseRequest) -> str:
    """Stream chunks, emit final/done messages, and record history."""
    history_user = (
        request.history_user_utterance if request.history_user_utterance is not None else request.user_utterance
    )
    state = _StreamState(
        completion_text=request.initial_text,
        is_text_visible=bool(request.initial_text) and request.is_initial_text_sent,
    )
    is_history_committed = False

    def _commit_history() -> None:
        """Commit streamed text to history at most once."""
        nonlocal is_history_committed
        is_history_commit_needed = bool(state.is_text_visible and state.completion_text)
        if is_history_committed or not is_history_commit_needed:
            return
        request.session_runtime.history.append_response(
            request.connection_state,
            history_user,
            state.completion_text,
        )
        is_history_committed = True

    try:
        await _send_initial_text(
            request.websocket,
            request.initial_text,
            state,
            is_already_sent=request.is_initial_text_sent,
        )
        if not state.is_interrupted:
            await _forward_stream_chunks(request.websocket, request.stream, state)
        if not state.is_interrupted:
            if not state.completion_text:
                await _handle_empty_output(request.websocket)
                return state.completion_text
            await _send_completion_frames(request.websocket, state)
    finally:
        _commit_history()
    return state.completion_text


__all__ = [
    "StreamResponseRequest",
    "build_flat_message",
    "safe_send_flat",
    "safe_send_json",
    "safe_send_text",
    "stream_response",
]
