"""Unit tests for websocket authentication logic."""

from __future__ import annotations

import time
import pytest
import asyncio
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
import src.websocket.authentication as authentication_module
from src.runtime.config import AuthenticationSettings, WebSocketSettings

if TYPE_CHECKING:
    from collections import deque
    from fastapi import WebSocket
    from collections.abc import Callable


class _FakeWebSocket:
    def __init__(self, *, headers: dict[str, str], host: str = "127.0.0.1") -> None:
        self.headers = headers
        self.client = SimpleNamespace(host=host)


def _run_authentication(
    headers: dict[str, str],
    *,
    authentication_settings: AuthenticationSettings,
    websocket_settings: WebSocketSettings,
    authentication_failures: dict[str, deque[float]],
    clock: Callable[[], float] = time.monotonic,
) -> bool:
    websocket = _FakeWebSocket(headers=headers)
    policy = authentication_module.build_authentication_policy(
        authentication_settings=authentication_settings,
        websocket_settings=websocket_settings,
        authentication_failures=authentication_failures,
        clock=clock,
    )
    return asyncio.run(
        authentication_module.authenticate_websocket(
            cast("WebSocket", websocket),
            policy=policy,
        ),
    )


def _authentication_settings(
    *,
    key: str = "secret",
) -> AuthenticationSettings:
    normalized_key = key.strip()
    if not normalized_key:
        raise ValueError
    return AuthenticationSettings(api_key=normalized_key)


def _websocket_settings(
    *,
    maximum_failures: int = 20,
    window_seconds: float = 60.0,
) -> WebSocketSettings:
    return WebSocketSettings(
        maximum_connections=None,
        idle_timeout_seconds=150.0,
        watchdog_tick_seconds=10.0,
        handshake_acquire_timeout_seconds=0.5,
        protocol_version=1,
        maximum_message_bytes=65536,
        authentication_failures_per_window=maximum_failures,
        rate_limit_window_seconds=window_seconds,
        maximum_messages_per_window=20,
        maximum_cancels_per_window=20,
    )


def test_authentication_outcomes() -> None:
    """Test websocket authentication accepts valid headers and rejects invalid inputs."""
    if (
        _run_authentication(
            {"x-api-key": "secret"},
            authentication_settings=_authentication_settings(),
            websocket_settings=_websocket_settings(),
            authentication_failures={},
        )
        is not True
    ):
        pytest.fail("Assertion failed")
    if (
        _run_authentication(
            {"authorization": "Bearer secret"},
            authentication_settings=_authentication_settings(),
            websocket_settings=_websocket_settings(),
            authentication_failures={},
        )
        is not True
    ):
        pytest.fail("Assertion failed")
    if (
        _run_authentication(
            {},
            authentication_settings=_authentication_settings(),
            websocket_settings=_websocket_settings(),
            authentication_failures={},
        )
        is not False
    ):
        pytest.fail("Assertion failed")
    websocket_settings = _websocket_settings()
    if (
        _run_authentication(
            {"x-api-key": "secret", "origin": "https://denied.example"},
            authentication_settings=_authentication_settings(),
            websocket_settings=websocket_settings,
            authentication_failures={},
        )
        is not True
    ):
        pytest.fail("Assertion failed")


def test_authentication_throttling() -> None:
    """Test authentication throttles repeated failures."""
    websocket_settings = _websocket_settings(maximum_failures=2, window_seconds=60.0)
    authentication_failures: dict[str, deque[float]] = {}

    def fixed_clock() -> float:
        """Return a fixed test clock value."""
        current_time = 100.0
        if current_time < 0:
            raise ValueError
        return current_time

    if (
        _run_authentication(
            {"x-api-key": "bad"},
            authentication_settings=_authentication_settings(),
            websocket_settings=websocket_settings,
            authentication_failures=authentication_failures,
            clock=fixed_clock,
        )
        is not False
    ):
        pytest.fail("Assertion failed")
    if (
        _run_authentication(
            {"x-api-key": "bad"},
            authentication_settings=_authentication_settings(),
            websocket_settings=websocket_settings,
            authentication_failures=authentication_failures,
            clock=fixed_clock,
        )
        is not False
    ):
        pytest.fail("Assertion failed")

    # Third attempt is throttled even with a valid key.
    if (
        _run_authentication(
            {"x-api-key": "secret"},
            authentication_settings=_authentication_settings(),
            websocket_settings=websocket_settings,
            authentication_failures=authentication_failures,
            clock=fixed_clock,
        )
        is not False
    ):
        pytest.fail("Assertion failed")
