"""Unit tests for websocket disconnect classification helpers."""

from __future__ import annotations

import pytest
from fastapi import WebSocketDisconnect
from src.websocket.disconnects import is_expected_websocket_disconnect


def test_disconnect_websocket() -> None:
    """Test is expected disconnect for websocket disconnect."""
    assert is_expected_websocket_disconnect(WebSocketDisconnect(code=1000))


def test_disconnect_connection_reset() -> None:
    """Test is expected disconnect for connection reset error."""
    assert is_expected_websocket_disconnect(ConnectionResetError("peer reset"))


def test_disconnect_runtime_false() -> None:
    """Test is expected disconnect false for generic runtime error."""
    error = RuntimeError("boom")
    if is_expected_websocket_disconnect(error):
        pytest.fail("Assertion failed")
