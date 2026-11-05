"""Default constants for test utilities.

This module contains hardcoded defaults for benchmarks, warmup/live tests,
sampling parameters, and prompt profiles. These values are used when no
environment override is provided and serve as the baseline configuration
for all test scripts.
"""

from __future__ import annotations

WARMUP_DEFAULT_MESSAGE = "hey there! how are you today?"
BENCHMARK_DEFAULT_MESSAGE = "who was Columbus?"

SERVER_URL_DEFAULT = "ws://127.0.0.1:8000/ws"
GENDER_DEFAULT = "female"
PERSONALITY_DEFAULT = "flirty"
TRANSACTION_TIMEOUT_SECONDS = 120.0
PING_INTERVAL_SECONDS_DEFAULT = 20
PING_TIMEOUT_SECONDS_DEFAULT = 20

BENCHMARK_DEFAULT_REQUESTS = 16
BENCHMARK_DEFAULT_CONCURRENCY = 8

# Idle test sanity defaults
IDLE_WAIT_SECONDS_DEFAULT = 3.0
IDLE_EXPECT_SECONDS_DEFAULT = 150.0
IDLE_GRACE_SECONDS_DEFAULT = 15.0

# Cancel test defaults
CANCEL_POST_SECONDS_DEFAULT = 2.0  # Seconds to wait after cancel before recovery
CANCEL_RECEIVE_SECONDS_DEFAULT = 30.0  # Timeout for each receive phase
CANCEL_CLIENT_COUNT_DEFAULT = 3  # Number of concurrent clients
CANCEL_REQUEST_DELAY_SECONDS = 1.0  # Seconds to collect tokens before cancel
CANCEL_DRAIN_SECONDS_DEFAULT = 2.0  # Seconds to verify no spurious messages after cancel

# WebSocket defaults
DEFAULT_WEBSOCKET_PATH = "/ws"

# Progress bar display
PROGRESS_BAR_WIDTH = 30

# WebSocket queue limit (None = unlimited)
WEBSOCKET_MAX_QUEUE = None

# WebSocket idle close behavior
WEBSOCKET_IDLE_CLOSE_CODE = 4000
WEBSOCKET_IDLE_CLOSE_REASON = "idle_timeout"

__all__ = [
    "BENCHMARK_DEFAULT_CONCURRENCY",
    "BENCHMARK_DEFAULT_MESSAGE",
    "BENCHMARK_DEFAULT_REQUESTS",
    "CANCEL_CLIENT_COUNT_DEFAULT",
    "CANCEL_DRAIN_SECONDS_DEFAULT",
    "CANCEL_POST_SECONDS_DEFAULT",
    "CANCEL_RECEIVE_SECONDS_DEFAULT",
    "CANCEL_REQUEST_DELAY_SECONDS",
    "DEFAULT_WEBSOCKET_PATH",
    "GENDER_DEFAULT",
    "IDLE_EXPECT_SECONDS_DEFAULT",
    "IDLE_GRACE_SECONDS_DEFAULT",
    "IDLE_WAIT_SECONDS_DEFAULT",
    "PERSONALITY_DEFAULT",
    "PING_INTERVAL_SECONDS_DEFAULT",
    "PING_TIMEOUT_SECONDS_DEFAULT",
    "PROGRESS_BAR_WIDTH",
    "SERVER_URL_DEFAULT",
    "TRANSACTION_TIMEOUT_SECONDS",
    "WARMUP_DEFAULT_MESSAGE",
    "WEBSOCKET_IDLE_CLOSE_CODE",
    "WEBSOCKET_IDLE_CLOSE_REASON",
    "WEBSOCKET_MAX_QUEUE",
]
