"""Unit tests for session task supervision."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
import asyncio
from unittest.mock import AsyncMock

import pytest
from fastapi import WebSocketDisconnect

from src.session.state import SessionState
from src.session.requests import spawn_session_task, abort_session_requests
from config.runtime.websocket import WEBSOCKET_ERROR_INTERNAL
from src.websocket.supervision import supervise_turn
from tests.suites.unit.builders import RecordingWebSocket, typed_websocket

if TYPE_CHECKING:
    from collections.abc import Callable, Awaitable

    from fastapi import WebSocket


async def _spawn_task(
    websocket: WebSocket,
    state: SessionState,
    *,
    request_id: str,
    operation: Callable[[], Awaitable[None]],
) -> asyncio.Task[None] | None:
    """Compose protocol reporting with session-owned task tracking.

    Args:
        websocket: WebSocket connection of the client.
        state: State of the session or test run.
        request_id: ID of the request.
        operation: Function to run.

    Returns:
        Protocol reporting with session-owned task tracking.

    """
    return await spawn_session_task(
        state,
        request_id=request_id,
        operation=lambda: supervise_turn(websocket, operation, request_id=request_id, state=state),
    )


async def _run_tracked_task(request_id: str, operation: Callable[[], Awaitable[None]]) -> RecordingWebSocket:
    """Await a supervised task, check it released its tracking slots, and return the socket it wrote to.

    Args:
        request_id: ID of the request.
        operation: Function to run.

    Returns:
        The socket it wrote to.

    """
    websocket = RecordingWebSocket()
    state = SessionState(meta={})

    task = await _spawn_task(typed_websocket(websocket), state, request_id=request_id, operation=operation)

    assert task is not None
    await task
    if state.active_request_id is not None:
        pytest.fail("Assertion failed")
    if state.active_request_task is not None:
        pytest.fail("Assertion failed")
    return websocket


async def _success_operation() -> None:
    delay = 0
    await asyncio.sleep(delay)


async def _failing_operation() -> None:
    message = "boom"
    error = RuntimeError(message)
    raise error


async def _disconnect_operation() -> None:
    raise WebSocketDisconnect


def test_task_supervision_outcomes() -> None:
    """Test spawn session task cleanup and internal error handling."""
    websocket = asyncio.run(_run_tracked_task("req-success", _success_operation))
    assert websocket.sent == []

    websocket = asyncio.run(_run_tracked_task("req-fail", _failing_operation))
    assert len(websocket.sent) == 1
    payload = json.loads(websocket.sent[0])
    assert payload["type"] == "error"
    assert payload["code"] == WEBSOCKET_ERROR_INTERNAL


def test_task_disconnect_ignored() -> None:
    """Test spawn session task swallows expected disconnect errors."""
    websocket = asyncio.run(_run_tracked_task("req-disconnect", _disconnect_operation))
    assert websocket.sent == []


def test_closed_session_rejection() -> None:
    """Reject closed sessions before constructing an operation coroutine."""
    operation = AsyncMock()
    state = SessionState(meta={}, lifecycle_state="closed")
    task = asyncio.run(
        _spawn_task(typed_websocket(RecordingWebSocket()), state, request_id="closed", operation=operation),
    )
    assert task is None
    operation.assert_not_called()


def test_immediate_cancellation() -> None:
    """Immediate cancellation clears tracking without starting generation."""

    async def scenario() -> None:
        """Cancel in the same event-loop turn that creates the request task."""
        operation = AsyncMock()
        engine = AsyncMock()
        state = SessionState(meta={})
        task = await _spawn_task(
            typed_websocket(RecordingWebSocket()),
            state,
            request_id="cancel",
            operation=operation,
        )
        await abort_session_requests(state, engine)
        assert task is not None
        assert task.cancelled()
        assert state.lifecycle_state == "idle"
        assert state.active_request_task is None
        assert state.active_request_id is None
        operation.assert_not_called()
        engine.abort.assert_awaited_once_with("cancel")

    asyncio.run(scenario())
