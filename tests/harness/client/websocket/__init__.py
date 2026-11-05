"""Static WebSocket helper exports for test clients."""

from __future__ import annotations

from .stream import record_token, consume_stream, finalize_metrics
from .message import (
    message_text,
    iter_messages,
    parse_message,
    dispatch_message,
    bootstrap_session,
    send_initial_user_turn,
)
from .payloads import build_end_payload, build_start_payload, build_cancel_payload, build_message_payload
from .connection import (
    read_api_key,
    open_websocket,
    send_end_frame,
    connect_websocket,
    receive_raw_frame,
    build_websocket_url,
    build_api_key_headers,
)

__all__ = [
    "bootstrap_session",
    "build_api_key_headers",
    "build_cancel_payload",
    "build_end_payload",
    "build_message_payload",
    "build_start_payload",
    "build_websocket_url",
    "connect_websocket",
    "consume_stream",
    "dispatch_message",
    "finalize_metrics",
    "iter_messages",
    "message_text",
    "open_websocket",
    "parse_message",
    "read_api_key",
    "receive_raw_frame",
    "record_token",
    "send_end_frame",
    "send_initial_user_turn",
]
