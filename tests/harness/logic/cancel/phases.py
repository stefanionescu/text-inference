"""Phase execution functions for cancel test.

This module provides async functions for each test phase:
- Cancel phase: send start, wait, send cancel, verify cancelled acknowledgement
- Drain phase: verify no spurious messages after cancel
- Recovery phase: send another request, verify full response
"""

from __future__ import annotations

import json
import time
from typing import TYPE_CHECKING, Any
import asyncio
import logging
from functools import partial
from dataclasses import dataclass

from websockets.exceptions import ConnectionClosed

from tests.state import StreamState, SessionContext, DrainPhaseResult, CancelPhaseResult, RecoveryPhaseResult
from tests.harness.client.websocket import (
    iter_messages,
    dispatch_message,
    finalize_metrics,
    build_start_payload,
    build_cancel_payload,
    build_message_payload,
    send_initial_user_turn,
)
from tests.harness.reporting.terminal import dim, write_line

from .callbacks import build_phase_callbacks

if TYPE_CHECKING:
    from collections.abc import Callable, Awaitable

    from websockets import WebSocketClientProtocol

    from .callbacks import DispatchResult, MessageCallback

logger = logging.getLogger(__name__)


@dataclass
class CancelLoop:
    """Mutable state for the cancel receive loop."""

    is_cancel_sent: bool = False
    is_cancelled: bool = False
    error: str | None = None


async def _send_cancel_if_due(
    websocket: WebSocketClientProtocol,
    loop: CancelLoop,
    *,
    start_time: float,
    cancel_delay_seconds: float,
) -> None:
    if loop.is_cancel_sent:
        return
    elapsed = time.perf_counter() - start_time
    if elapsed < cancel_delay_seconds:
        return
    cancel_payload = build_cancel_payload()
    await websocket.send(json.dumps(cancel_payload))
    loop.is_cancel_sent = True
    write_line(dim(f"  [cancel] sent cancel after {elapsed:.1f}s"))


async def _dispatch_until_done(
    websocket: WebSocketClientProtocol,
    callbacks: dict[str, MessageCallback],
    *,
    receive_timeout_seconds: float,
    after_message: Callable[[], Awaitable[None]] | None = None,
) -> DispatchResult:
    """Feed frames to the callbacks until one reports completion; a stream that just ends reports nothing."""
    async for message in iter_messages(websocket, receive_timeout_seconds=receive_timeout_seconds):
        result = await dispatch_message(
            message,
            callbacks,
            default=lambda _message: True,
        )
        if after_message is not None:
            await after_message()

        if isinstance(result, dict) and result.get("is_done"):
            return result
    return {}


async def _consume_cancel_messages(
    websocket: WebSocketClientProtocol,
    state: StreamState,
    *,
    receive_timeout_seconds: float,
    cancel_delay_seconds: float,
) -> CancelLoop:
    callbacks = build_phase_callbacks(state, is_recovery=False)
    loop = CancelLoop()
    start_time = time.perf_counter()

    try:
        result = await _dispatch_until_done(
            websocket,
            callbacks,
            receive_timeout_seconds=receive_timeout_seconds,
            after_message=partial(
                _send_cancel_if_due,
                websocket,
                loop,
                start_time=start_time,
                cancel_delay_seconds=cancel_delay_seconds,
            ),
        )
    except TimeoutError:
        loop.error = f"timeout after {receive_timeout_seconds:.1f}s"
    except ConnectionClosed as exception:
        loop.error = f"connection closed: {exception.code}"
    else:
        loop.is_cancelled = result.get("cancelled", False)
        loop.error = result.get("error")

    return loop


async def consume_recovery_stream(
    websocket: WebSocketClientProtocol,
    state: StreamState,
    *,
    receive_timeout_seconds: float,
) -> tuple[dict[str, Any], str | None, bool]:
    """Stream one full response into state; a timeout or closed socket comes back as an error string."""
    callbacks = build_phase_callbacks(state, is_recovery=True)
    is_cancelled = False
    error: str | None = None
    metrics: dict[str, Any] = {}

    try:
        result = await _dispatch_until_done(websocket, callbacks, receive_timeout_seconds=receive_timeout_seconds)
    except TimeoutError:
        error = f"timeout after {receive_timeout_seconds:.1f}s"
        metrics = finalize_metrics(state, is_cancelled=True)
    except ConnectionClosed as exception:
        error = f"connection closed: {exception.code}"
        metrics = finalize_metrics(state, is_cancelled=True)
    else:
        is_cancelled = result.get("cancelled", False)
        error = result.get("error")
        metrics = result.get("metrics", {})

    return metrics, error, is_cancelled


async def run_cancel_phase(
    websocket: WebSocketClientProtocol,
    context: SessionContext,
    user_message: str,
    receive_timeout_seconds: float,
    cancel_delay_seconds: float,
) -> CancelPhaseResult:
    """Execute the cancel phase: send start, wait, then send cancel.

    Args:
        websocket: WebSocket connection.
        context: Session context for building payloads.
        user_message: User message to send.
        receive_timeout_seconds: Timeout for receiving messages.
        cancel_delay_seconds: Seconds to wait before sending cancel.

    Returns:
        Result of the cancel phase.

    """
    state = StreamState()
    start_payload = build_start_payload(context)
    async with asyncio.timeout(receive_timeout_seconds):
        await send_initial_user_turn(
            websocket,
            start_payload,
            user_message,
            sampling=context.sampling,
        )
    write_line(dim("  [cancel] bootstrapped session and sent first message..."))

    loop = await _consume_cancel_messages(
        websocket,
        state,
        receive_timeout_seconds=receive_timeout_seconds,
        cancel_delay_seconds=cancel_delay_seconds,
    )
    has_passed = loop.is_cancelled and loop.error is None

    status_parts = [f"cancelled={loop.is_cancelled}"]
    if state.chunks > 0:
        status_parts.append(f"tokens={state.chunks}")
    if len(state.completion_text) > 0:
        status_parts.append(f"chars={len(state.completion_text)}")
    write_line(dim(f"  [cancel] received done ({', '.join(status_parts)})"))

    return CancelPhaseResult(
        has_passed=has_passed,
        is_cancelled=loop.is_cancelled,
        tokens_received=state.chunks,
        chars_received=len(state.completion_text),
        error=loop.error,
    )


async def run_drain_phase(
    websocket: WebSocketClientProtocol,
    drain_timeout_seconds: float,
) -> DrainPhaseResult:
    """Verify no spurious messages arrive after cancel acknowledgement.

    This phase waits for drain_timeout_seconds. If ANY message arrives,
    the test fails. Success means timing out with no messages received.

    Args:
        websocket: WebSocket connection.
        drain_timeout_seconds: Seconds to wait for potential spurious messages.

    Returns:
        Result of the drain phase.

    """
    write_line(dim(f"  [drain] checking for spurious messages ({drain_timeout_seconds:.1f}s)..."))
    spurious_count = 0
    spurious_types: list[str] = []

    try:
        async for message in iter_messages(websocket, receive_timeout_seconds=drain_timeout_seconds):
            raw_message_type = message.get("type", "unknown")
            message_type = raw_message_type if isinstance(raw_message_type, str) else "unknown"
            spurious_count += 1
            spurious_types.append(message_type)
            logger.warning("Spurious message after cancel: type=%s", message_type)
    except TimeoutError:
        # Timeout is expected and means success
        pass
    except ConnectionClosed:
        # Connection closed is acceptable during drain
        pass

    has_passed = spurious_count == 0
    error = None
    if not has_passed:
        error = f"received {spurious_count} spurious message(s): {spurious_types}"

    if has_passed:
        write_line(dim("  [drain] no spurious messages"))
    else:
        write_line(dim(f"  [drain] FAILED: {error}"))

    return DrainPhaseResult(
        has_passed=has_passed,
        spurious_messages=spurious_count,
        error=error,
    )


async def run_recovery_phase(
    websocket: WebSocketClientProtocol,
    context: SessionContext,
    user_message: str,
    receive_timeout_seconds: float,
    post_cancel_wait_seconds: float,
) -> RecoveryPhaseResult:
    """Execute the recovery phase: wait, send start, stream full response.

    Args:
        websocket: WebSocket connection.
        context: Session context for building payloads.
        user_message: User message to send.
        receive_timeout_seconds: Timeout for receiving messages.
        post_cancel_wait_seconds: Seconds to wait before sending recovery request.

    Returns:
        Result of the recovery phase.

    """
    write_line(dim(f"  [recovery] waiting {post_cancel_wait_seconds:.1f}s before request..."))
    await asyncio.sleep(post_cancel_wait_seconds)

    state = StreamState()

    recovery_payload = build_message_payload(user_message, sampling=context.sampling)
    await websocket.send(json.dumps(recovery_payload))
    write_line(dim("  [recovery] sent message..."))

    metrics, error, is_cancelled = await consume_recovery_stream(
        websocket,
        state,
        receive_timeout_seconds=receive_timeout_seconds,
    )

    has_response = len(state.completion_text) > 0
    has_passed = not is_cancelled and has_response and error is None

    return RecoveryPhaseResult(
        has_passed=has_passed,
        response_text=state.completion_text,
        metrics=metrics,
        error=error,
    )


__all__ = ["consume_recovery_stream", "run_cancel_phase", "run_drain_phase", "run_recovery_phase"]
