"""Tracing and error reporting for WebSocket turn operations."""

from __future__ import annotations

import time
import asyncio
import logging
import contextlib
from typing import TYPE_CHECKING
from src.websocket.errors import send_error
from src.telemetry.sentry import capture_error
from src.telemetry.instruments import get_metrics
from config.runtime.websocket import WEBSOCKET_ERROR_INTERNAL
from src.telemetry.error_classification import classify_error
from src.telemetry.traces import RequestSpanAttributes, request_span
from src.websocket.disconnects import is_expected_websocket_disconnect

if TYPE_CHECKING:
    from fastapi import WebSocket
    from src.session.state import SessionState
    from collections.abc import Awaitable, Callable

logger = logging.getLogger(__name__)


async def supervise_turn(
    websocket: WebSocket,
    operation: Callable[[], Awaitable[None]],
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
            await operation()
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


__all__ = ["supervise_turn"]
