"""Unit tests for websocket lifecycle idle-timeout signaling."""

from __future__ import annotations

import asyncio

import pytest

from src.websocket.lifecycle import WebSocketLifecycle
from config.runtime.websocket import WEBSOCKET_CLOSE_IDLE_REASON
from tests.suites.unit.builders import typed_websocket


class _FakeWebSocket:
    def __init__(self) -> None:
        self.close_calls: list[tuple[int, str]] = []

    async def close(self, *, code: int, reason: str) -> None:
        """Test close.

        Args:
            code: Error or close code.
            reason: Reason text to report.

        """
        self.close_calls.append((code, reason))


def test_lifecycle_idle_close() -> None:
    """Test lifecycle sets idle timeout flag and closes socket."""

    async def _run() -> None:
        websocket = _FakeWebSocket()
        lifecycle = WebSocketLifecycle(
            typed_websocket(websocket),
            idle_timeout_seconds=0.02,
            watchdog_tick_seconds=0.005,
            idle_close_code=4444,
        )
        lifecycle.start()
        await asyncio.sleep(0.06)
        await lifecycle.stop()

        assert lifecycle.has_idle_timed_out()
        assert websocket.close_calls == [(4444, WEBSOCKET_CLOSE_IDLE_REASON)]

    asyncio.run(_run())


def test_lifecycle_stop_early() -> None:
    """Test lifecycle stop before timeout does not mark idle timeout."""

    async def _run() -> None:
        websocket = _FakeWebSocket()
        lifecycle = WebSocketLifecycle(
            typed_websocket(websocket),
            idle_timeout_seconds=1.0,
            watchdog_tick_seconds=0.05,
        )
        lifecycle.start()
        await asyncio.sleep(0.01)
        await lifecycle.stop()

        if lifecycle.has_idle_timed_out():
            pytest.fail("Assertion failed")
        assert websocket.close_calls == []

    asyncio.run(_run())
