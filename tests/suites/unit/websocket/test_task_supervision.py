"""Unit tests for session task supervision."""

from __future__ import annotations

import json
import pytest
import asyncio
from typing import TYPE_CHECKING, cast
from fastapi import WebSocketDisconnect
from src.state.session import SessionState
from src.websocket.supervision import spawn_session_task
from config.runtime.websocket import WEBSOCKET_ERROR_INTERNAL

if TYPE_CHECKING:
    from fastapi import WebSocket


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

        task = await spawn_session_task(
            cast("WebSocket", websocket),
            state,
            request_id="req-success",
            operation=_success_operation(),
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

        task = await spawn_session_task(
            cast("WebSocket", websocket),
            state,
            request_id="req-fail",
            operation=_failing_operation(),
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

        task = await spawn_session_task(
            cast("WebSocket", websocket),
            state,
            request_id="req-disconnect",
            operation=_disconnect_operation(),
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
