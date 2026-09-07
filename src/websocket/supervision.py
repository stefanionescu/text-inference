"""WebSocket-scoped supervision for background turn execution."""

from __future__ import annotations

import time
import asyncio
import logging
import contextlib
from typing import TYPE_CHECKING, Any
from src.websocket.errors import send_error
from src.telemetry.sentry import capture_error
from src.telemetry.instruments import get_metrics
from config.runtime.websocket import WEBSOCKET_ERROR_INTERNAL
from src.telemetry.error_classification import classify_error
from src.telemetry.traces import RequestSpanAttributes, request_span
from src.websocket.disconnects import is_expected_websocket_disconnect
from src.session.requests import attach_request_task, begin_session_request, cleanup_session_requests

if TYPE_CHECKING:
    from fastapi import WebSocket
    from collections.abc import Awaitable
    from src.state.session import SessionState

logger = logging.getLogger(__name__)


async def _run_supervised(
    websocket: WebSocket,
    operation: Awaitable[Any],
    *,
    request_id: str,
    state: SessionState,
) -> None:
    """Run a request operation with tracing, metrics, and error handling."""
    started_at = time.perf_counter()
    model = str(state.meta.get("model") or "")
    client_id = str(state.meta.get("client_id") or "")
    with request_span(
        RequestSpanAttributes(
            request_id=request_id,
            session_id=state.session_id,
            client_id=client_id,
            model=model,
        ),
    ):
        try:
            await operation
        except asyncio.CancelledError:
            raise
        except Exception as exception:
            if is_expected_websocket_disconnect(exception):
                logger.info("Session task ended after disconnect (%s)", exception.__class__.__name__)
                return
            capture_error(exception)
            error_type = classify_error(exception)
            metrics = get_metrics()
            metrics.errors_total.add(1, {"error.type": error_type})
            metrics.phase_errors_total.add(1, {"phase": "turn", "error.type": error_type})
            logger.exception("Session task failed")
            with contextlib.suppress(Exception):
                await send_error(
                    websocket,
                    code=WEBSOCKET_ERROR_INTERNAL,
                    message="An unexpected server error occurred.",
                )
        finally:
            get_metrics().phase_latency.record(max(0.0, time.perf_counter() - started_at), {"phase": "turn"})
            with contextlib.suppress(Exception):
                async with state.request_lock:
                    cleanup_session_requests(state, request_id=request_id, is_forced=False)


async def spawn_session_task(
    websocket: WebSocket,
    state: SessionState,
    *,
    request_id: str,
    operation: Awaitable[Any],
) -> asyncio.Task[Any] | None:
    """Create, supervise, and track a session-scoped background task."""
    async with state.request_lock:
        started = begin_session_request(state, request_id)
    if not started:
        return None

    task = asyncio.create_task(
        _run_supervised(
            websocket,
            operation,
            request_id=request_id,
            state=state,
        ),
    )
    async with state.request_lock:
        attach_request_task(state, request_id=request_id, task=task)
    return task


__all__ = ["spawn_session_task"]
