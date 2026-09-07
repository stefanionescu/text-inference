"""Streaming token metrics tracking and consumption.

This module provides functions for tracking streaming token metrics and
consuming WebSocket response streams. Uses StreamState from metrics for
payload storage.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any
from .message import iter_messages, message_text
from tests.harness.client.errors import StreamError
from tests.harness.metrics import round_milliseconds
from tests.harness.client.text_detection import contains_complete_sentence, has_minimum_word_count

if TYPE_CHECKING:
    from tests.state.metrics import StreamState
    from websockets import WebSocketClientProtocol


# ============================================================================
# Internal Helpers
# ============================================================================


def _milliseconds_since_sent(state: StreamState, timestamp: float | None) -> float | None:
    """Calculate milliseconds elapsed since the request was sent."""
    if timestamp is None:
        return None
    return (timestamp - state.sent_timestamp) * 1000.0


# ============================================================================
# Stream Tracking Functions
# ============================================================================


def record_token(state: StreamState, chunk: str) -> dict[str, float | None]:
    """Record a streaming token and return any newly triggered metrics."""
    metrics: dict[str, float | None] = {}
    if not chunk:
        return metrics

    if state.first_token_timestamp is None:
        state.first_token_timestamp = time.perf_counter()
        metrics["ttfb_ms"] = _milliseconds_since_sent(state, state.first_token_timestamp)

    state.completion_text += chunk

    if state.first_three_words_timestamp is None and has_minimum_word_count(state.completion_text, 3):
        state.first_three_words_timestamp = time.perf_counter()
        metrics["time_to_first_3_words_ms"] = _milliseconds_since_sent(state, state.first_three_words_timestamp)

    if state.first_sentence_timestamp is None and contains_complete_sentence(state.completion_text):
        state.first_sentence_timestamp = time.perf_counter()
        metrics["time_to_first_complete_sentence_ms"] = _milliseconds_since_sent(state, state.first_sentence_timestamp)

    state.chunks += 1
    return metrics


def finalize_metrics(state: StreamState, *, is_cancelled: bool = False) -> dict[str, Any]:
    """Build the final metrics dict after streaming completes."""
    done_timestamp = time.perf_counter()
    first_byte_latency_milliseconds = _milliseconds_since_sent(state, state.first_token_timestamp)
    stream_milliseconds = None
    if state.first_token_timestamp is not None:
        stream_milliseconds = (done_timestamp - state.first_token_timestamp) * 1000.0
    total_milliseconds = (done_timestamp - state.sent_timestamp) * 1000.0
    return {
        "ok": not is_cancelled,
        "ttfb_ms": round_milliseconds(first_byte_latency_milliseconds),
        "total_ms": round_milliseconds(total_milliseconds),
        "stream_ms": round_milliseconds(stream_milliseconds),
        "time_to_first_complete_sentence_ms": round_milliseconds(
            _milliseconds_since_sent(state, state.first_sentence_timestamp),
        ),
        "time_to_first_3_words_ms": round_milliseconds(
            _milliseconds_since_sent(state, state.first_three_words_timestamp),
        ),
        "chunks": state.chunks,
        "chars": len(state.completion_text),
    }


# ============================================================================
# Stream Consumption
# ============================================================================


async def consume_stream(websocket: WebSocketClientProtocol, state: StreamState) -> str:
    """Consume streaming response until done message, tracking metrics."""
    async for message in iter_messages(websocket):
        message_type = message.get("type")

        if message_type == "token":
            record_token(state, message_text(message, "text", default="") or "")
            continue

        if message_type == "final":
            completion_text = message_text(message, "text")
            if completion_text:
                state.completion_text = completion_text
            continue

        if message_type == "done":
            return state.completion_text

        if message_type == "cancelled":
            return state.completion_text

        if message_type == "error":
            raise StreamError(message)

    error_message = "WebSocket closed before receiving 'done'"
    raise RuntimeError(error_message)


__all__ = [
    "consume_stream",
    "finalize_metrics",
    "record_token",
]
