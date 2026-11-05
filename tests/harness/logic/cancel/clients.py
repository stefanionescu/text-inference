"""Client flow orchestration for cancel test.

This module provides async functions that orchestrate the full lifecycle
of each client type:
- Canceling client: cancel phase -> drain phase -> recovery phase
- Normal client: stream full response -> wait for coordination
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
import asyncio
from dataclasses import dataclass

from websockets.exceptions import ConnectionClosed, WebSocketException

from tests.state import (
    StreamState,
    SessionContext,
    DrainPhaseResult,
    CancelPhaseResult,
    CancelClientResult,
    NormalClientResult,
    RecoveryPhaseResult,
)
from tests.harness.client.websocket import (
    iter_messages,
    open_websocket,
    send_end_frame,
    dispatch_message,
    finalize_metrics,
    connect_websocket,
    build_start_payload,
    send_initial_user_turn,
)
from tests.harness.reporting.terminal import dim, write_line
from tests.harness.environment.settings import (
    DEFAULT_PING_TIMEOUT_SECONDS,
    DEFAULT_PING_INTERVAL_SECONDS,
)

from .phases import run_drain_phase, run_cancel_phase, run_recovery_phase
from .callbacks import build_recovery_callbacks

if TYPE_CHECKING:
    from websockets import WebSocketClientProtocol


@dataclass(frozen=True)
class NormalClientRequest:
    """Inputs for one normal cancel-suite client."""

    server_url: str
    authentication_headers: dict[str, str]
    context: SessionContext
    client_id: int
    user_message: str
    receive_timeout_seconds: float
    wait_for_recovery: asyncio.Event


@dataclass(frozen=True)
class CancelingClientRequest:
    """Inputs for the canceling cancel-suite client."""

    server_url: str
    authentication_headers: dict[str, str]
    context: SessionContext
    user_message: str
    cancel_delay_seconds: float
    drain_timeout_seconds: float
    post_cancel_wait_seconds: float
    receive_timeout_seconds: float
    recovery_done: asyncio.Event


async def _consume_recovery_stream(
    websocket: WebSocketClientProtocol,
    *,
    receive_timeout_seconds: float,
) -> tuple[str, dict[str, Any], str | None, bool]:
    state = StreamState()
    callbacks = build_recovery_callbacks(state)
    is_cancelled = False
    error: str | None = None
    metrics: dict[str, Any] = {}

    try:
        async for message in iter_messages(websocket, receive_timeout_seconds=receive_timeout_seconds):
            result = await dispatch_message(
                message,
                callbacks,
                default=lambda _message: True,
            )

            if isinstance(result, dict) and result.get("is_done"):
                is_cancelled = result.get("cancelled", False)
                error = result.get("error")
                metrics = result.get("metrics", {})
                break

    except TimeoutError:
        error = f"timeout after {receive_timeout_seconds:.1f}s"
        metrics = finalize_metrics(state, is_cancelled=True)
    except ConnectionClosed as exception:
        error = f"connection closed: {exception.code}"
        metrics = finalize_metrics(state, is_cancelled=True)

    return state.completion_text, metrics, error, is_cancelled


def _normal_result(
    request: NormalClientRequest,
    *,
    has_passed: bool,
    response_text: str,
    metrics: dict[str, Any],
    error: str | None,
) -> NormalClientResult:
    return NormalClientResult(
        client_id=request.client_id,
        has_passed=has_passed,
        response_text=response_text,
        metrics=metrics,
        error=error,
    )


async def _run_normal_session(websocket: WebSocketClientProtocol, request: NormalClientRequest) -> NormalClientResult:
    label = f"client-{request.client_id}"
    start_payload = build_start_payload(request.context)
    async with asyncio.timeout(request.receive_timeout_seconds):
        await send_initial_user_turn(
            websocket,
            start_payload,
            request.user_message,
            sampling=request.context.sampling,
        )
    write_line(dim(f"  [{label}] bootstrapped session and sent first message..."))

    response_text, metrics, error, is_cancelled = await _consume_recovery_stream(
        websocket,
        receive_timeout_seconds=request.receive_timeout_seconds,
    )
    has_passed = not is_cancelled and bool(response_text) and error is None

    if has_passed:
        write_line(dim(f"  [{label}] completed, waiting for cancel recovery..."))
    else:
        reason = error or "empty response or cancelled"
        write_line(dim(f"  [{label}] FAILED: {reason}"))

    await request.wait_for_recovery.wait()
    await send_end_frame(websocket)

    return _normal_result(
        request,
        has_passed=has_passed,
        response_text=response_text,
        metrics=metrics,
        error=error,
    )


async def run_normal_client(request: NormalClientRequest) -> NormalClientResult:
    """Run a client that completes inference normally and waits for coordination.

    Args:
        request: Normal client connection and flow inputs.

    Returns:
        Result of the normal client flow.

    """
    try:
        async with open_websocket(
            lambda: connect_websocket(
                request.server_url,
                headers=request.authentication_headers,
                max_queue=None,
                ping_interval=DEFAULT_PING_INTERVAL_SECONDS,
                ping_timeout=DEFAULT_PING_TIMEOUT_SECONDS,
            ),
        ) as websocket:
            return await _run_normal_session(websocket, request)

    except (OSError, TimeoutError, RuntimeError, ValueError, WebSocketException) as exception:
        return _normal_result(
            request,
            has_passed=False,
            response_text="",
            metrics={},
            error=f"connection failed: {exception}",
        )


def _skipped_drain(error: str) -> DrainPhaseResult:
    return DrainPhaseResult(has_passed=False, spurious_messages=0, error=error)


def _skipped_recovery(error: str) -> RecoveryPhaseResult:
    return RecoveryPhaseResult(has_passed=False, response_text="", metrics={}, error=error)


async def _run_canceling_session(
    websocket: WebSocketClientProtocol, request: CancelingClientRequest
) -> CancelClientResult:
    cancel_result = await run_cancel_phase(
        websocket,
        request.context,
        request.user_message,
        request.receive_timeout_seconds,
        request.cancel_delay_seconds,
    )

    if cancel_result.has_passed:
        drain_result = await run_drain_phase(websocket, request.drain_timeout_seconds)
    else:
        drain_result = _skipped_drain("skipped due to cancel failure")

    if drain_result.has_passed:
        recovery_result = await run_recovery_phase(
            websocket,
            request.context,
            request.user_message,
            request.receive_timeout_seconds,
            request.post_cancel_wait_seconds,
        )
    else:
        recovery_result = _skipped_recovery("skipped due to drain failure")

    request.recovery_done.set()
    await send_end_frame(websocket)

    return CancelClientResult(
        cancel_phase=cancel_result,
        drain_phase=drain_result,
        recovery_phase=recovery_result,
    )


async def run_canceling_client(request: CancelingClientRequest) -> CancelClientResult:
    """Run the client that performs cancel, drain verification, and recovery.

    Args:
        request: Canceling client connection and flow inputs.

    Returns:
        Combined result of cancel, drain, and recovery phases.

    """
    cancel_result = CancelPhaseResult(
        has_passed=False,
        is_cancelled=False,
        tokens_received=0,
        chars_received=0,
        error="connection failed",
    )
    drain_result = _skipped_drain("skipped")
    recovery_result = _skipped_recovery("skipped")

    try:
        async with open_websocket(
            lambda: connect_websocket(
                request.server_url,
                headers=request.authentication_headers,
                max_queue=None,
                ping_interval=DEFAULT_PING_INTERVAL_SECONDS,
                ping_timeout=DEFAULT_PING_TIMEOUT_SECONDS,
            ),
        ) as websocket:
            return await _run_canceling_session(websocket, request)

    except (OSError, TimeoutError, RuntimeError, ValueError, WebSocketException) as exception:
        cancel_result = CancelPhaseResult(
            has_passed=False,
            is_cancelled=False,
            tokens_received=0,
            chars_received=0,
            error=f"connection failed: {exception}",
        )
        request.recovery_done.set()

    return CancelClientResult(
        cancel_phase=cancel_result,
        drain_phase=drain_result,
        recovery_phase=recovery_result,
    )


__all__ = ["CancelingClientRequest", "NormalClientRequest", "run_canceling_client", "run_normal_client"]
