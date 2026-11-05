"""Unit tests for websocket client message parsing."""

from __future__ import annotations

import json

import pytest

from src.websocket.parser import parse_client_message
from config.runtime.websocket import WEBSOCKET_PROTOCOL_VERSION, WEBSOCKET_MAX_MESSAGE_BYTES
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS


def _valid_start(**overrides: object) -> str:
    base: dict[str, object] = {
        "type": "start",
        "v": WEBSOCKET_PROTOCOL_VERSION,
        "gender": "female",
        "personality": "calm",
        "prompt": "hello",
    }
    base.update(overrides)
    return json.dumps(base)


def test_rejects_message_envelopes() -> None:
    """Test invalid message envelopes are rejected."""
    with pytest.raises(ValueError, match="Empty message"):
        parse_client_message("", websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket)
    with pytest.raises(ValueError, match="Empty message"):
        parse_client_message("   ", websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket)
    with pytest.raises(ValueError, match="valid JSON"):
        parse_client_message("{bad json", websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket)
    with pytest.raises(TypeError, match="JSON object"):
        parse_client_message('"hello"', websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket)
    with pytest.raises(TypeError, match="JSON object"):
        parse_client_message("[1, 2]", websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket)


def test_rejects_start_metadata() -> None:
    """Test start payload metadata validation."""
    with pytest.raises(ValueError, match="Missing 'type'"):
        parse_client_message(
            json.dumps({"v": WEBSOCKET_PROTOCOL_VERSION, "gender": "female"}),
            websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket,
        )
    with pytest.raises(ValueError, match=r"Invalid payload field 'start\.v'"):
        parse_client_message(
            json.dumps({"type": "start", "gender": "female"}), websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket
        )
    with pytest.raises(ValueError, match="unsupported protocol version"):
        parse_client_message(
            json.dumps({"type": "start", "v": WEBSOCKET_PROTOCOL_VERSION + 1, "gender": "female"}),
            websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket,
        )


def test_valid_socket_payloads() -> None:
    """Test valid start and message payload normalization."""
    result = parse_client_message(_valid_start(type="START"), websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket)
    assert result["type"] == "start"
    result = parse_client_message(_valid_start(), websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket)
    assert result["type"] == "start"
    assert result["v"] == WEBSOCKET_PROTOCOL_VERSION
    assert result["gender"] == "female"
    result = parse_client_message(
        json.dumps({"type": "message", "v": WEBSOCKET_PROTOCOL_VERSION, "user_utterance": "hello"}),
        websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket,
    )
    assert result["type"] == "message"
    assert result["user_utterance"] == "hello"


def test_start_history_size() -> None:
    """Test start accepts history content while the message fits the byte limit."""
    empty_payload_size = len(_valid_start(history=[{"role": "user", "content": ""}]).encode())
    history = [{"role": "user", "content": "x" * (WEBSOCKET_MAX_MESSAGE_BYTES - empty_payload_size - 1)}]
    payload = _valid_start(history=history)

    assert len(payload.encode()) < WEBSOCKET_MAX_MESSAGE_BYTES

    result = parse_client_message(payload, websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket)

    assert result["history"] == history


def test_rejects_start_fields() -> None:
    """Test invalid start-only field combinations are rejected."""
    with pytest.raises(ValueError, match="user_utterance"):
        parse_client_message(
            _valid_start(user_utterance="hello"), websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket
        )
    with pytest.raises(ValueError, match="custom_field"):
        parse_client_message(
            json.dumps(
                {
                    "type": "start",
                    "v": WEBSOCKET_PROTOCOL_VERSION,
                    "gender": "male",
                    "personality": "calm",
                    "prompt": "hello",
                    "custom_field": "value",
                },
            ),
            websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket,
        )


def test_message_size_limit() -> None:
    """Test message payload size limit."""
    huge = "x" * (WEBSOCKET_MAX_MESSAGE_BYTES + 1)
    with pytest.raises(ValueError, match="exceeds max size"):
        parse_client_message(huge, websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket)
