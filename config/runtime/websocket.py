"""WebSocket-specific runtime configuration values.

This module defines constants for WebSocket connection lifecycle management:

Timeouts:
    WEBSOCKET_IDLE_TIMEOUT_SECONDS: Close connections after this many seconds of inactivity.
        This prevents resource leaks from abandoned connections.

    WEBSOCKET_WATCHDOG_TICK_SECONDS: How often the idle watchdog checks activity.
        Lower values = more responsive timeout, higher CPU usage.

    WEBSOCKET_HANDSHAKE_ACQUIRE_TIMEOUT_SECONDS: Max time to wait for connection slot.
        If the server is at capacity, connections wait this long before
        being rejected.

Close Codes (RFC 6455):
    1000: Normal closure (client requested)
    1008: Policy violation (auth failure)
    1013: Try again later (server at capacity)
    4000+: Application-defined (idle timeout)

Environment Variables:
    All values can be overridden. The defaults provide a balance between
    responsiveness and resource efficiency.
"""

from __future__ import annotations

# ============================================================================
# Timeout Configuration
# ============================================================================

WEBSOCKET_IDLE_TIMEOUT_SECONDS = 150.0  # 2.5 minutes
WEBSOCKET_WATCHDOG_TICK_SECONDS = 10.0  # Check every 10s
HANDSHAKE_ACQUIRE_TIMEOUT_SECONDS = 0.5
WEBSOCKET_PROTOCOL_VERSION = 1
WEBSOCKET_MAX_MESSAGE_BYTES = 65536
WEBSOCKET_RATE_WINDOW_SECONDS = 60.0
WEBSOCKET_MESSAGES_PER_WINDOW = 20
WEBSOCKET_CANCELS_PER_WINDOW = 20
AUTHENTICATION_FAILURE_LIMIT = 10

# ============================================================================
# WebSocket Close Codes
# ============================================================================
# These follow RFC 6455 conventions where possible.

WEBSOCKET_CLOSE_UNAUTHORIZED_CODE = 1008  # Policy violation
WEBSOCKET_CLOSE_BUSY_CODE = 1013  # Try again later
WEBSOCKET_CLOSE_IDLE_CODE = 4000  # Application-defined
WEBSOCKET_CLOSE_IDLE_REASON = "idle_timeout"
WEBSOCKET_CLIENT_CLOSE_CODE = 1000  # Normal

# ============================================================================
# Message Types
# ============================================================================

WEBSOCKET_TYPE_START = "start"
WEBSOCKET_TYPE_CANCEL = "cancel"
WEBSOCKET_TYPE_MESSAGE = "message"
WEBSOCKET_TYPE_PING = "ping"
WEBSOCKET_TYPE_PONG = "pong"
WEBSOCKET_TYPE_END = "end"
WEBSOCKET_TYPE_ERROR = "error"
# reason: This protocol message type label is not a credential.
WEBSOCKET_TYPE_TOKEN = "token"
WEBSOCKET_TYPE_COMPLETION = "final"
WEBSOCKET_TYPE_DONE = "done"
WEBSOCKET_TYPE_CANCELLED = "cancelled"

# ============================================================================
# Error Codes (payload "code" values)
# ============================================================================

AUTHENTICATION_FAILURE_CODE = "authentication_failed"
WEBSOCKET_ERROR_SERVER_BUSY = "server_at_capacity"
WEBSOCKET_ERROR_INVALID_MESSAGE = "invalid_message"
WEBSOCKET_ERROR_INVALID_PAYLOAD = "invalid_payload"
WEBSOCKET_ERROR_INVALID_SETTINGS = "invalid_settings"
WEBSOCKET_ERROR_RATE_LIMITED = "rate_limited"
WEBSOCKET_ERROR_QUEUE_FULL = "queue_full"
TEXT_LENGTH_ERROR_CODE = "text_too_long"
WEBSOCKET_ERROR_INVALID_VOICE = "invalid_voice"
WEBSOCKET_ERROR_INTERNAL = "internal_error"

# ============================================================================
# HTTP-Style Status Codes
# ============================================================================

WEBSOCKET_STATUS_OK = 200
WEBSOCKET_STATUS_BAD_REQUEST = 400
WEBSOCKET_STATUS_UNAUTHORIZED = 401
WEBSOCKET_STATUS_RATE_LIMITED = 429
WEBSOCKET_STATUS_INTERNAL = 500
WEBSOCKET_STATUS_UNAVAILABLE = 503

# Mapping from error string codes to numeric status
ERROR_CODE_TO_STATUS: dict[str, int] = {
    "authentication_failed": 401,
    "server_at_capacity": 503,
    "invalid_message": 400,
    "invalid_payload": 400,
    "invalid_settings": 400,
    "rate_limited": 429,
    "queue_full": 503,
    "text_too_long": 400,
    "invalid_voice": 400,
    "internal_error": 500,
}

__all__ = [
    "AUTHENTICATION_FAILURE_CODE",
    "AUTHENTICATION_FAILURE_LIMIT",
    "ERROR_CODE_TO_STATUS",
    "HANDSHAKE_ACQUIRE_TIMEOUT_SECONDS",
    "TEXT_LENGTH_ERROR_CODE",
    "WEBSOCKET_CANCELS_PER_WINDOW",
    "WEBSOCKET_CLIENT_CLOSE_CODE",
    "WEBSOCKET_CLOSE_BUSY_CODE",
    "WEBSOCKET_CLOSE_IDLE_CODE",
    "WEBSOCKET_CLOSE_IDLE_REASON",
    "WEBSOCKET_CLOSE_UNAUTHORIZED_CODE",
    "WEBSOCKET_ERROR_INTERNAL",
    "WEBSOCKET_ERROR_INVALID_MESSAGE",
    "WEBSOCKET_ERROR_INVALID_PAYLOAD",
    "WEBSOCKET_ERROR_INVALID_SETTINGS",
    "WEBSOCKET_ERROR_INVALID_VOICE",
    "WEBSOCKET_ERROR_QUEUE_FULL",
    "WEBSOCKET_ERROR_RATE_LIMITED",
    "WEBSOCKET_ERROR_SERVER_BUSY",
    "WEBSOCKET_IDLE_TIMEOUT_SECONDS",
    "WEBSOCKET_MAX_MESSAGE_BYTES",
    "WEBSOCKET_MESSAGES_PER_WINDOW",
    "WEBSOCKET_PROTOCOL_VERSION",
    "WEBSOCKET_RATE_WINDOW_SECONDS",
    "WEBSOCKET_STATUS_BAD_REQUEST",
    "WEBSOCKET_STATUS_INTERNAL",
    "WEBSOCKET_STATUS_OK",
    "WEBSOCKET_STATUS_RATE_LIMITED",
    "WEBSOCKET_STATUS_UNAUTHORIZED",
    "WEBSOCKET_STATUS_UNAVAILABLE",
    "WEBSOCKET_TYPE_CANCEL",
    "WEBSOCKET_TYPE_CANCELLED",
    "WEBSOCKET_TYPE_COMPLETION",
    "WEBSOCKET_TYPE_DONE",
    "WEBSOCKET_TYPE_END",
    "WEBSOCKET_TYPE_ERROR",
    "WEBSOCKET_TYPE_MESSAGE",
    "WEBSOCKET_TYPE_PING",
    "WEBSOCKET_TYPE_PONG",
    "WEBSOCKET_TYPE_START",
    "WEBSOCKET_TYPE_TOKEN",
    "WEBSOCKET_WATCHDOG_TICK_SECONDS",
]
