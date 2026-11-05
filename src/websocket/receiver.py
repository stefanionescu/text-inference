"""WebSocket receiver and dispatch helpers."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
import logging
import contextlib
from dataclasses import dataclass

from src.session.requests import has_running_task, abort_session_requests
from config.runtime.websocket import WEBSOCKET_STATUS_OK, WEBSOCKET_CLIENT_CLOSE_CODE, WEBSOCKET_ERROR_INVALID_MESSAGE

from .errors import send_error
from .parser import parse_client_message
from .transport import safe_send_flat
from .disconnects import is_expected_websocket_disconnect
from ..messages.turn import TurnMessageRequest, handle_turn_message
from ..telemetry.instruments import get_metrics
from .rate_limiting.messages import consume_limiter, select_rate_limiter

if TYPE_CHECKING:
    from fastapi import WebSocket

    from src.session.state import SessionState
    from src.runtime.dependencies import RuntimeDependencies

    from .lifecycle import WebSocketLifecycle
    from .rate_limiting.window import SlidingWindowRateLimiter

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SessionDispatch:
    """Inputs needed to dispatch one session message."""

    websocket: WebSocket
    message_type: str
    message: dict[str, Any]
    state: SessionState
    is_started: bool
    runtime_dependencies: RuntimeDependencies


async def _handle_control_message(
    websocket: WebSocket,
    message_type: str,
) -> bool:
    """Process ping/pong/end messages; return True if connection should close."""
    if message_type == "ping":
        await safe_send_flat(websocket, "pong")
        return False
    if message_type == "pong":
        return False
    if message_type == "end":
        logger.info("WS recv: end")
        await safe_send_flat(websocket, "done", status=WEBSOCKET_STATUS_OK)
        with contextlib.suppress(Exception):
            await websocket.close(code=WEBSOCKET_CLIENT_CLOSE_CODE)
        return True
    return False


async def _parse_incoming(websocket: WebSocket, raw_message: str) -> dict[str, Any] | None:
    """Parse raw text into a flat message dict or None on error."""
    started_at = time.perf_counter()
    try:
        parsed = parse_client_message(raw_message, websocket_settings=websocket.app.state.settings.websocket)
        get_metrics().phase_latency.record(max(0.0, time.perf_counter() - started_at), {"phase": "parse"})
    except (TypeError, ValueError) as exception:
        metrics = get_metrics()
        metrics.phase_latency.record(max(0.0, time.perf_counter() - started_at), {"phase": "parse"})
        metrics.phase_errors_total.add(1, {"phase": "parse", "error.type": "invalid_payload"})
        await send_error(websocket, code=WEBSOCKET_ERROR_INVALID_MESSAGE, message=str(exception))
        return None
    else:
        return parsed


async def _apply_rate_limit(
    websocket: WebSocket,
    message_type: str,
    message_limiter: SlidingWindowRateLimiter,
    cancel_limiter: SlidingWindowRateLimiter,
) -> bool:
    """Apply the appropriate rate limiter for one message type."""
    limiter = select_rate_limiter(message_type, message_limiter, cancel_limiter)
    if limiter is None:
        return True
    return await consume_limiter(websocket, limiter)


async def _handle_start_command(dispatch: SessionDispatch) -> bool:
    """Process an initial start command and return session-start state."""
    if dispatch.is_started:
        await send_error(
            dispatch.websocket,
            code=WEBSOCKET_ERROR_INVALID_MESSAGE,
            message="start may only be sent once per connection; use 'message' for subsequent turns.",
        )
        return True
    get_metrics().requests_total.add(1, {"status": "started"})
    return await handle_turn_message(
        TurnMessageRequest(
            websocket=dispatch.websocket,
            message=dispatch.message,
            state=dispatch.state,
            message_type="start",
            runtime_dependencies=dispatch.runtime_dependencies,
        ),
    )


async def _handle_message_command(dispatch: SessionDispatch) -> bool:
    """Process a follow-up message command."""
    if not dispatch.is_started:
        await send_error(
            dispatch.websocket,
            code=WEBSOCKET_ERROR_INVALID_MESSAGE,
            message="no active session; send 'start' first.",
        )
        return False
    get_metrics().requests_total.add(1, {"status": "continued"})
    if has_running_task(dispatch.state):
        await abort_session_requests(dispatch.state, dispatch.runtime_dependencies.engine)
    await handle_turn_message(
        TurnMessageRequest(
            websocket=dispatch.websocket,
            message=dispatch.message,
            state=dispatch.state,
            message_type="message",
            runtime_dependencies=dispatch.runtime_dependencies,
        ),
    )
    return True


async def _handle_turn_command(dispatch: SessionDispatch) -> bool:
    """Process start or message commands and return the updated started flag."""
    if dispatch.message_type == "start":
        return await _handle_start_command(dispatch)
    if dispatch.message_type == "message":
        return await _handle_message_command(dispatch)
    return dispatch.is_started


async def _dispatch_session_message(dispatch: SessionDispatch) -> bool:
    """Dispatch a session message. Returns the new 'started' flag."""
    if dispatch.message_type in {"start", "message"}:
        return await _handle_turn_command(dispatch)
    if dispatch.message_type == "cancel":
        get_metrics().cancellation_total.add(1)
        logger.info("WS recv: cancel")
        await abort_session_requests(dispatch.state, dispatch.runtime_dependencies.engine)
        await safe_send_flat(dispatch.websocket, "cancelled")
        return dispatch.is_started
    await send_error(
        dispatch.websocket,
        code=WEBSOCKET_ERROR_INVALID_MESSAGE,
        message=f"Message type '{dispatch.message_type}' is not supported.",
    )
    return dispatch.is_started


async def run_receiver(
    websocket: WebSocket,
    lifecycle: WebSocketLifecycle,
    rate_limiters: tuple[SlidingWindowRateLimiter, SlidingWindowRateLimiter],
    runtime_dependencies: RuntimeDependencies,
    *,
    state: SessionState,
) -> None:
    """Receive and dispatch messages using the connection-owned session state."""
    message_limiter, cancel_limiter = rate_limiters
    is_started = False

    while True:
        try:
            raw_message = await websocket.receive_text()
        except Exception as exception:
            if lifecycle.has_idle_timed_out() or is_expected_websocket_disconnect(exception):
                break
            raise

        message = await _parse_incoming(websocket, raw_message)
        if message is None:
            continue

        lifecycle.touch()
        message_type = message["type"]

        if not await _apply_rate_limit(websocket, message_type, message_limiter, cancel_limiter):
            continue
        if message_type in {"ping", "pong", "end"}:
            if await _handle_control_message(websocket, message_type):
                break
            continue
        is_started = await _dispatch_session_message(
            SessionDispatch(
                websocket=websocket,
                message_type=message_type,
                message=message,
                state=state,
                is_started=is_started,
                runtime_dependencies=runtime_dependencies,
            ),
        )


__all__ = ["run_receiver"]
