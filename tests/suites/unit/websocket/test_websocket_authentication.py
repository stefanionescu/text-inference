"""Unit tests for websocket authentication logic."""

from __future__ import annotations

import time
from types import SimpleNamespace
from typing import TYPE_CHECKING
import asyncio
from functools import partial

import pytest

from src.runtime.config import WebSocketSettings, AuthenticationSettings
from tests.suites.unit.builders import typed_websocket
import src.websocket.authentication as authentication_module

if TYPE_CHECKING:
    from collections import deque
    from collections.abc import Callable


class _FakeWebSocket:
    def __init__(self, *, headers: dict[str, str], host: str = "127.0.0.1") -> None:
        self.headers = headers
        self.client = SimpleNamespace(host=host)


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


def _run_authentication(
    headers: dict[str, str],
    *,
    websocket_settings: WebSocketSettings | None = None,
    authentication_failures: dict[str, deque[float]] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> bool:
    """Authenticate one connection against the API key "secret", by default with no earlier failures."""
    websocket = _FakeWebSocket(headers=headers)
    policy = authentication_module.build_authentication_policy(
        authentication_settings=AuthenticationSettings(api_key="secret"),
        websocket_settings=websocket_settings or _websocket_settings(),
        authentication_failures={} if authentication_failures is None else authentication_failures,
        clock=clock,
    )
    return asyncio.run(
        authentication_module.authenticate_websocket(
            typed_websocket(websocket),
            policy=policy,
        ),
    )


@pytest.mark.parametrize(
    ("headers", "is_authenticated"),
    [
        ({"x-api-key": "secret"}, True),
        ({"authorization": "Bearer secret"}, True),
        ({}, False),
        ({"x-api-key": "secret", "origin": "https://denied.example"}, True),
    ],
)
def test_authentication_outcomes(headers: dict[str, str], *, is_authenticated: bool) -> None:
    """Test websocket authentication accepts valid headers and rejects invalid inputs."""
    assert _run_authentication(headers) is is_authenticated


def test_authentication_throttling() -> None:
    """Test authentication throttles repeated failures."""
    authentication_failures: dict[str, deque[float]] = {}
    attempt = partial(
        _run_authentication,
        websocket_settings=_websocket_settings(maximum_failures=2, window_seconds=60.0),
        authentication_failures=authentication_failures,
        clock=lambda: 100.0,
    )

    assert attempt({"x-api-key": "bad"}) is False
    assert attempt({"x-api-key": "bad"}) is False

    # Third attempt is throttled even with a valid key.
    assert attempt({"x-api-key": "secret"}) is False
