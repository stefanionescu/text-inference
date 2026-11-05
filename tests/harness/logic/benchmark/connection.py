"""WebSocket connection handling for benchmark transactions.

This module provides the core transaction execution logic over WebSocket
connections. It handles connection setup, message sending, response streaming,
and error handling for benchmark runs.
"""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING, Any
import asyncio

from websockets.exceptions import ConnectionClosedOK, ConnectionClosedError

from tests.state import StreamState, SessionContext, BenchmarkConfig
from config.tests.defaults import WEBSOCKET_MAX_QUEUE
from tests.harness.metrics import error_result
from tests.harness.client.errors import ServerError
from tests.harness.client.websocket import (
    record_token,
    iter_messages,
    open_websocket,
    send_end_frame,
    finalize_metrics,
    connect_websocket,
    build_start_payload,
    build_websocket_url,
    build_api_key_headers,
    build_message_payload,
    send_initial_user_turn,
)

if TYPE_CHECKING:
    from websockets import WebSocketClientProtocol


async def _run_phase(
    websocket: WebSocketClientProtocol,
    config: BenchmarkConfig,
    phase: int,
    session_id: str,
) -> dict[str, Any]:
    """Execute a single transaction phase with timeout handling."""
    try:
        return await asyncio.wait_for(
            _send_stream(websocket, config, phase, session_id),
            timeout=config.timeout_seconds,
        )
    except TimeoutError:
        return error_result("timeout", phase=phase)
    except (OSError, RuntimeError, ValueError, TypeError) as exception:
        return error_result(str(exception), phase=phase)


async def _send_stream(
    websocket: WebSocketClientProtocol,
    config: BenchmarkConfig,
    phase: int,
    session_id: str,
) -> dict[str, Any]:
    """Bootstrap the first phase or send a message turn, then stream the response."""
    if phase == 1:
        context = SessionContext(
            session_id=session_id,
            gender=config.gender,
            personality=config.personality,
            prompt=config.prompt,
            sampling=config.sampling,
        )
        await send_initial_user_turn(
            websocket,
            build_start_payload(context),
            config.message,
            sampling=config.sampling,
        )
    else:
        await websocket.send(json.dumps(build_message_payload(config.message, sampling=config.sampling)))
    state = StreamState()

    return await _consume_stream(websocket, state, phase)


async def _consume_stream(
    websocket: WebSocketClientProtocol,
    state: StreamState,
    phase: int,
) -> dict[str, Any]:
    """Consume the response stream and collect metrics."""
    result: dict[str, Any] | None = None
    try:
        async for message in iter_messages(websocket):
            result = _handle_stream_message(message, state, phase)
            if result is not None:
                break

    except ConnectionClosedOK:
        result = error_result("connection_closed_ok", phase=phase)
    except ConnectionClosedError as exception:
        result = error_result(f"connection_closed: code={exception.code}", phase=phase)

    return result or error_result("stream ended before 'done'", phase=phase)


def _handle_stream_message(message: dict[str, Any], state: StreamState, phase: int) -> dict[str, Any] | None:
    """Handle one benchmark stream message."""
    message_type = message.get("type")
    result = None
    if message_type == "token":
        record_token(state, message.get("text", ""))
    elif message_type == "final":
        normalized = message.get("normalized_text")
        if normalized:
            state.completion_text = normalized
    elif message_type == "done":
        result = _build_success_result(finalize_metrics(state, is_cancelled=False), phase)
    elif message_type == "cancelled":
        result = _build_success_result(finalize_metrics(state, is_cancelled=True), phase)
    elif message_type == "error":
        result = _build_error_result(message, phase)
    return result


def _build_success_result(metrics: dict[str, Any], phase: int) -> dict[str, Any]:
    """Build a success result from tracker metrics."""
    return {
        "ok": metrics.get("ok", True),
        "phase": phase,
        "ttfb_ms": metrics.get("ttfb_ms"),
        "first_sentence_ms": metrics.get("time_to_first_complete_sentence_ms"),
        "first_three_words_ms": metrics.get("time_to_first_3_words_ms"),
    }


def _build_error_result(message: dict[str, Any], phase: int) -> dict[str, Any]:
    """Build an error result from a server error message."""
    error = ServerError.decode_message(message)
    return {
        "ok": False,
        "phase": phase,
        "error": str(error),
        "error_code": error.error_code,
        "recoverable": error.is_recoverable(),
    }


async def run_connection(config: BenchmarkConfig) -> list[dict[str, Any]]:
    """Execute one or two transactions over a single WebSocket connection."""
    phases = 2 if config.is_double_ttfb_enabled else 1
    results: list[dict[str, Any]] = []
    authenticated_url = build_websocket_url(config.server_url, api_key=config.api_key)
    authentication_headers = build_api_key_headers(api_key=config.api_key)

    session_id = f"bench-{uuid.uuid4()}"
    try:
        async with open_websocket(
            lambda: connect_websocket(
                authenticated_url,
                headers=authentication_headers,
                max_queue=WEBSOCKET_MAX_QUEUE,
            ),
        ) as websocket:
            try:
                for phase in range(1, phases + 1):
                    result = await _run_phase(websocket, config, phase, session_id)
                    results.append(result)
                    if not result.get("ok"):
                        break
            finally:
                await send_end_frame(websocket)
    except (ConnectionClosedOK, ConnectionClosedError) as exception:
        if not results:
            return [error_result(f"connection_closed: {exception}", phase=1)]
    except (OSError, RuntimeError, ValueError, TypeError) as exception:
        if not results:
            return [error_result(f"connection_failed: {exception}", phase=1)]

    return results or [error_result("connection_failed", phase=1)]


__all__ = ["run_connection"]
