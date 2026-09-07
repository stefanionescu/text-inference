"""Primary WebSocket connection handler orchestration.

This module contains the main WebSocket connection handler that serves as
the entry point for all client connections. It orchestrates connection setup,
receiver dispatch, and cleanup on disconnect.
"""

from __future__ import annotations

import time
import contextlib
from logging import getLogger
from typing import TYPE_CHECKING
from dataclasses import dataclass
from .receiver import run_receiver
from ..logging import set_log_context
from .lifecycle import WebSocketLifecycle
from ..telemetry.traces import session_span
from ..telemetry.instruments import get_metrics
from .errors import reject_connection, send_error
from fastapi import WebSocket, WebSocketDisconnect
from src.session.requests import close_session_requests
from .disconnects import is_expected_websocket_disconnect
from .rate_limiting.window import SlidingWindowRateLimiter
from ..telemetry.error_classification import classify_error
from ..telemetry.sentry import add_breadcrumb, capture_error
from .authentication import authenticate_websocket, build_authentication_policy
from config.runtime.websocket import (
    WEBSOCKET_ERROR_INTERNAL,
    WEBSOCKET_CLOSE_BUSY_CODE,
    AUTHENTICATION_FAILURE_CODE,
    WEBSOCKET_ERROR_SERVER_BUSY,
    WEBSOCKET_CANCELS_PER_WINDOW,
    WEBSOCKET_MESSAGES_PER_WINDOW,
    WEBSOCKET_CLOSE_UNAUTHORIZED_CODE,
    WEBSOCKET_RATE_LIMIT_WINDOW_SECONDS,
)

if TYPE_CHECKING:
    from src.state.session import SessionState
    from src.runtime.dependencies import RuntimeDependencies

logger = getLogger(__name__)


@dataclass(frozen=True)
class ConnectionFinalization:
    """Inputs for WebSocket connection teardown."""

    websocket: WebSocket
    runtime_dependencies: RuntimeDependencies
    lifecycle: WebSocketLifecycle | None
    state: SessionState | None
    is_admitted: bool
    generation_count: int = 0


async def _prepare_connection(websocket: WebSocket, runtime_dependencies: RuntimeDependencies) -> bool:
    """Authenticate and admit a WebSocket connection."""
    connections = runtime_dependencies.connections
    if not await authenticate_websocket(
        websocket,
        policy=build_authentication_policy(
            authentication_settings=runtime_dependencies.settings.authentication,
            websocket_settings=runtime_dependencies.settings.websocket,
        ),
    ):
        await reject_connection(
            websocket,
            code=AUTHENTICATION_FAILURE_CODE,
            message=(
                "Authentication required. Provide valid API key via "
                "'X-API-Key' header or 'Authorization: Bearer <key>'."
            ),
            close_code=WEBSOCKET_CLOSE_UNAUTHORIZED_CODE,
        )
        return False

    if not await connections.connect(websocket):
        await reject_connection(
            websocket,
            code=WEBSOCKET_ERROR_SERVER_BUSY,
            message="Server cannot accept new connections. Please try again later.",
            close_code=WEBSOCKET_CLOSE_BUSY_CODE,
        )
        return False

    try:
        await websocket.accept()
    except (RuntimeError, WebSocketDisconnect):
        with contextlib.suppress(RuntimeError, WebSocketDisconnect):
            await connections.disconnect(websocket)
        raise
    return True


async def _cleanup_session(runtime_dependencies: RuntimeDependencies, state: SessionState) -> float:
    """Clean up session resources on disconnect and return duration."""
    started_at = time.perf_counter()
    session_runtime = runtime_dependencies.session_runtime
    duration = max(0.0, time.monotonic() - state.created_at)
    await session_runtime.abort_session_requests(state)
    async with state.request_lock:
        close_session_requests(state)
    get_metrics().phase_latency.record(max(0.0, time.perf_counter() - started_at), {"phase": "cleanup"})
    return duration


def _create_rate_limiters(
    runtime_dependencies: RuntimeDependencies | None = None,
) -> tuple[SlidingWindowRateLimiter, SlidingWindowRateLimiter]:
    """Initialize per-connection rate limiters."""
    websocket_settings = None if runtime_dependencies is None else runtime_dependencies.settings.websocket
    message_limiter = SlidingWindowRateLimiter(
        limit=WEBSOCKET_MESSAGES_PER_WINDOW
        if websocket_settings is None
        else websocket_settings.maximum_messages_per_window,
        window_seconds=WEBSOCKET_RATE_LIMIT_WINDOW_SECONDS
        if websocket_settings is None
        else websocket_settings.rate_limit_window_seconds,
    )
    cancel_limiter = SlidingWindowRateLimiter(
        limit=WEBSOCKET_CANCELS_PER_WINDOW
        if websocket_settings is None
        else websocket_settings.maximum_cancels_per_window,
        window_seconds=WEBSOCKET_RATE_LIMIT_WINDOW_SECONDS
        if websocket_settings is None
        else websocket_settings.rate_limit_window_seconds,
    )
    return message_limiter, cancel_limiter


async def _stop_lifecycle(lifecycle: WebSocketLifecycle | None) -> None:
    """Stop a lifecycle watchdog if one was started."""
    if lifecycle is not None:
        with contextlib.suppress(RuntimeError):
            await lifecycle.stop()


async def _cleanup_state(runtime_dependencies: RuntimeDependencies, state: SessionState | None) -> float:
    """Cleanup session state and return its duration."""
    if state is not None:
        try:
            return await _cleanup_session(runtime_dependencies, state)
        except (RuntimeError, OSError, ValueError) as exception:
            capture_error(exception)
            metrics = get_metrics()
            metrics.errors_total.add(1, {"error.type": "cleanup_failed"})
            metrics.phase_errors_total.add(1, {"phase": "cleanup", "error.type": "cleanup_failed"})
            logger.exception("WebSocket cleanup failed")
    return 0.0


async def _disconnect_admitted(finalization: ConnectionFinalization, session_duration: float) -> int:
    """Disconnect an admitted socket and return remaining connection count."""
    if not finalization.is_admitted:
        return 0

    metrics = get_metrics()
    connections = finalization.runtime_dependencies.connections
    metrics.active_connections.add(-1)
    metrics.connection_duration.record(session_duration)
    metrics.session_churn_total.add(1)
    if finalization.generation_count:
        metrics.generations_per_session.record(finalization.generation_count)

    with contextlib.suppress(RuntimeError, WebSocketDisconnect):
        await connections.disconnect(finalization.websocket)

    remaining = len(connections.active_connections)
    logger.info("WebSocket connection closed. Active: %s", remaining)
    return remaining


async def clear_after_last_disconnect(finalization: ConnectionFinalization, remaining: int) -> None:
    """Clear engine caches when the last client disconnects."""
    if remaining == 0:
        with contextlib.suppress(RuntimeError):
            await finalization.runtime_dependencies.clear_caches_on_disconnect()


async def _finalize_connection(finalization: ConnectionFinalization) -> None:
    """Run teardown actions after the connection loop exits."""
    await _stop_lifecycle(finalization.lifecycle)
    session_duration = await _cleanup_state(finalization.runtime_dependencies, finalization.state)
    remaining = await _disconnect_admitted(finalization, session_duration)
    if finalization.is_admitted:
        await clear_after_last_disconnect(finalization, remaining)


def _start_lifecycle(websocket: WebSocket, runtime_dependencies: RuntimeDependencies) -> WebSocketLifecycle:
    """Create and start the WebSocket lifecycle watchdog."""
    lifecycle = WebSocketLifecycle(
        websocket,
        idle_timeout_seconds=runtime_dependencies.settings.websocket.idle_timeout_seconds,
        watchdog_tick_seconds=runtime_dependencies.settings.websocket.watchdog_tick_seconds,
    )
    lifecycle.start()
    return lifecycle


async def _run_accepted_connection(
    websocket: WebSocket,
    runtime_dependencies: RuntimeDependencies,
    lifecycle: WebSocketLifecycle,
    client_id: str,
) -> SessionState | None:
    """Run the receiver for an admitted WebSocket connection."""
    metrics = get_metrics()
    metrics.active_connections.add(1)
    add_breadcrumb("Connection accepted", category="server")
    message_limiter, cancel_limiter = _create_rate_limiters(runtime_dependencies)

    logger.info(
        "WebSocket connection accepted. Active: %s",
        len(runtime_dependencies.connections.active_connections),
    )

    try:
        with session_span(client_id=client_id):
            return await run_receiver(
                websocket,
                lifecycle,
                message_limiter,
                cancel_limiter,
                runtime_dependencies,
            )
    except WebSocketDisconnect:
        return None
    except (RuntimeError, OSError, ValueError) as exception:
        if lifecycle.has_idle_timed_out() or is_expected_websocket_disconnect(exception):
            logger.info("WebSocket disconnected (%s)", exception.__class__.__name__)
            return None
        capture_error(exception)
        metrics.errors_total.add(1, {"error.type": classify_error(exception)})
        logger.exception("WebSocket error")
        with contextlib.suppress(RuntimeError, WebSocketDisconnect):
            await send_error(
                websocket,
                code=WEBSOCKET_ERROR_INTERNAL,
                message="An unexpected server error occurred.",
            )
        return None


async def handle_websocket_connection(websocket: WebSocket, runtime_dependencies: RuntimeDependencies) -> None:
    """Route one WebSocket connection through the message loop."""
    client = websocket.client
    client_id = f"{client.host}:{client.port}" if client else "unknown"
    tokens = set_log_context(client_id=client_id)
    lifecycle: WebSocketLifecycle | None = None
    is_admitted = False
    state: SessionState | None = None
    try:
        if not await _prepare_connection(websocket, runtime_dependencies):
            return

        is_admitted = True
        lifecycle = _start_lifecycle(websocket, runtime_dependencies)
        state = await _run_accepted_connection(
            websocket,
            runtime_dependencies,
            lifecycle,
            client_id,
        )
    finally:
        await _finalize_connection(
            ConnectionFinalization(
                websocket=websocket,
                runtime_dependencies=runtime_dependencies,
                lifecycle=lifecycle,
                state=state,
                is_admitted=is_admitted,
            ),
        )
        for var, token in tokens:
            var.reset(token)


__all__ = ["handle_websocket_connection"]
