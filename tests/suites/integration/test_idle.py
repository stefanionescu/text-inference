"""Integration tests for websocket idle-timeout behavior."""

from __future__ import annotations

import json
from dataclasses import replace

from config.runtime.websocket import WEBSOCKET_CLOSE_IDLE_CODE, WEBSOCKET_PROTOCOL_VERSION, WEBSOCKET_CLOSE_IDLE_REASON
from tests.suites.integration.builders import TEST_API_KEY, AUTHENTICATED_SETTINGS, open_test_client

_IDLE_SETTINGS = replace(
    AUTHENTICATED_SETTINGS,
    websocket=replace(
        AUTHENTICATED_SETTINGS.websocket,
        idle_timeout_seconds=0.2,
        watchdog_tick_seconds=0.02,
    ),
)


def test_idle_close_code() -> None:
    """Test idle connection closes with expected code and reason."""
    with (
        open_test_client(_IDLE_SETTINGS) as client,
        client.websocket_connect("/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket,
    ):
        close_frame = websocket.receive()

    assert close_frame["type"] == "websocket.close"
    assert close_frame["code"] == WEBSOCKET_CLOSE_IDLE_CODE
    assert close_frame["reason"] == WEBSOCKET_CLOSE_IDLE_REASON


def test_activity_keeps_alive() -> None:
    """Test activity keeps connection alive until explicit end."""
    with (
        open_test_client(_IDLE_SETTINGS) as client,
        client.websocket_connect("/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket,
    ):
        websocket.send_text(json.dumps({"type": "ping", "v": WEBSOCKET_PROTOCOL_VERSION}))
        assert json.loads(websocket.receive_text()) == {"type": "pong"}

        websocket.send_text(json.dumps({"type": "end", "v": WEBSOCKET_PROTOCOL_VERSION}))
        assert json.loads(websocket.receive_text()) == {"type": "done", "status": 200}
