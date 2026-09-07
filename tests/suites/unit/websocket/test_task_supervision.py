"""Unit tests for session task supervision."""

from __future__ import annotations

import json
import pytest
import asyncio
from unittest.mock import AsyncMock
from typing import TYPE_CHECKING, cast
from fastapi import WebSocketDisconnect
from src.session.state import SessionState
from src.websocket.supervision import supervise_turn
from config.runtime.websocket import WEBSOCKET_ERROR_INTERNAL
from src.session.requests import abort_session_requests, spawn_session_task

if TYPE_CHECKING:
    from fastapi import WebSocket
    from collections.abc import Awaitable, Callable


async def _spawn_task(
    websocket: WebSocket,
    state: SessionState,
    *,
    request_id: str,
    operation: Callable[[], Awaitable[None]],
) -> asyncio.Task[None] | None:
    """Compose protocol reporting with session-owned task tracking."""
    return await spawn_session_task(
        state,
        request_id=request_id,
        operation=lambda: supervise_turn(websocket, operation, request_id=request_id, state=state),
    )


class _NoopWebSocket:
    def __init__(self) -> None:
        self.sent: list[str] = []

    async def send_text(self, text: str) -> None:
        """Test send text."""
        sent = self.sent
        payload = text
        sent.append(payload)


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

    async def scenario() -> None:
        """Test scenario."""
        websocket = _NoopWebSocket()
        state = SessionState(meta={})

        task = await _spawn_task(
            cast("WebSocket", websocket),
            state,
            request_id="req-success",
            operation=_success_operation,
        )

        assert task is not None
        await task
        if state.active_request_id is not None:
            pytest.fail("Assertion failed")
        if state.active_request_task is not None:
            pytest.fail("Assertion failed")
        assert websocket.sent == []
        websocket = _NoopWebSocket()
        state = SessionState(meta={})

        task = await _spawn_task(
            cast("WebSocket", websocket),
            state,
            request_id="req-fail",
            operation=_failing_operation,
        )

        assert task is not None
        await task
        if state.active_request_id is not None:
            pytest.fail("Assertion failed")
        if state.active_request_task is not None:
            pytest.fail("Assertion failed")
        assert len(websocket.sent) == 1
        payload = json.loads(websocket.sent[0])
        assert payload["type"] == "error"
        assert payload["code"] == WEBSOCKET_ERROR_INTERNAL

    scenario_coro = scenario()
    asyncio.run(scenario_coro)


def test_task_disconnect_ignored() -> None:
    """Test spawn session task swallows expected disconnect errors."""

    async def scenario() -> None:
        """Test scenario."""
        websocket = _NoopWebSocket()
        state = SessionState(meta={})

        task = await _spawn_task(
            cast("WebSocket", websocket),
            state,
            request_id="req-disconnect",
            operation=_disconnect_operation,
        )

        assert task is not None
        await task
        if state.active_request_id is not None:
            pytest.fail("Assertion failed")
        if state.active_request_task is not None:
            pytest.fail("Assertion failed")
        assert websocket.sent == []

    scenario_coro = scenario()
    asyncio.run(scenario_coro)


def test_closed_session_rejection() -> None:
    """Reject closed sessions before constructing an operation coroutine."""
    operation = AsyncMock()
    state = SessionState(meta={}, lifecycle_state="closed")
    task = asyncio.run(
        _spawn_task(cast("WebSocket", _NoopWebSocket()), state, request_id="closed", operation=operation),
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
            cast("WebSocket", _NoopWebSocket()),
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
