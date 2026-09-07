"""Main test runner for history recall tests.

Connects to the server with a pre-built conversation history, then sends
follow-up messages to test the assistant's recall of earlier exchanges.
Tracks TTFB for each response and prints summary statistics.
"""

from __future__ import annotations

import json
import uuid
import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from tests.harness.client.prompt import select_prompt
from tests.harness.client.errors import ServerError, StreamError
from tests.state import SessionContext, StreamState, TTFBSamples
from tests.harness.messages.history import HISTORY_RECALL_MESSAGES, WARM_HISTORY
from tests.harness.metrics import emit_ttfb_summary, has_ttfb_samples, record_ttfb
from tests.harness.client.websocket import (
    consume_stream,
    send_end_frame,
    finalize_metrics,
    connect_websocket,
    build_start_payload,
    build_websocket_url,
    build_api_key_headers,
    build_message_payload,
    send_initial_user_turn,
)
from tests.harness.reporting.terminal import (
    dim,
    write_line,
    format_user,
    section_header,
    exchange_footer,
    exchange_header,
    format_assistant,
    format_metrics_inline,
)
from tests.harness.environment.settings import (
    DEFAULT_WEBSOCKET_PING_TIMEOUT_SECONDS,
    DEFAULT_WEBSOCKET_PING_INTERVAL_SECONDS,
)

if TYPE_CHECKING:
    from websockets import WebSocketClientProtocol


@dataclass(frozen=True)
class HistorySequence:
    """Inputs for one history recall sequence."""

    websocket: WebSocketClientProtocol
    session_id: str
    gender: str
    personality: str
    prompt: str | None
    sampling: dict[str, float | int] | None
    timeout_seconds: float
    ttfb_samples: TTFBSamples


@dataclass(frozen=True)
class HistoryRunRequest:
    """Connection and prompt inputs for one history replay."""

    server_url: str
    api_key: str | None
    gender: str
    personality: str
    timeout_seconds: float
    sampling: dict[str, float | int] | None


# ============================================================================
# Internal Helpers
# ============================================================================


async def _collect_response(websocket: WebSocketClientProtocol, state: StreamState) -> str:
    """Collect streaming response until done message, tracking metrics."""
    try:
        return await consume_stream(websocket, state)
    except StreamError as exception:
        raise ServerError.from_message(exception.message) from exception


def _print_exchange(
    index: int,
    user_text: str,
    reply: str,
    metrics: dict[str, Any],
) -> None:
    """Print a formatted exchange."""
    write_line(exchange_header(index=index))
    write_line(f"  {format_user(user_text)}")
    write_line(f"  {format_assistant(reply)}")
    write_line(f"  {format_metrics_inline(metrics)}")
    write_line(exchange_footer())


async def _send_message_request(
    sequence: HistorySequence,
    context: SessionContext,
    user_text: str,
    index: int,
) -> tuple[str, dict[str, Any]]:
    """Send a message request and collect the response with metrics tracking."""
    payload = build_message_payload(user_text, sampling=context.sampling)

    state = StreamState()
    async with asyncio.timeout(sequence.timeout_seconds):
        await sequence.websocket.send(json.dumps(payload))
        reply = await _collect_response(sequence.websocket, state)
    metrics = finalize_metrics(state)

    _print_exchange(index, user_text, reply, metrics)
    record_ttfb(sequence.ttfb_samples, metrics)
    return reply, metrics


def _print_header(
    personality: str,
    gender: str,
) -> None:
    """Print the test header."""
    write_line(f"\n{section_header('HISTORY RECALL TEST')}")
    write_line(dim(f"  warm history: {len(WARM_HISTORY)} messages"))
    write_line(dim(f"  recall tests: {len(HISTORY_RECALL_MESSAGES)} messages"))
    write_line(dim(f"  profile: {gender}/{personality}\n"))


async def _run_history_sequence(sequence: HistorySequence) -> None:
    """Run through all history recall messages."""
    history: list[dict[str, str]] = list(WARM_HISTORY)
    context = SessionContext(
        session_id=sequence.session_id,
        gender=sequence.gender,
        personality=sequence.personality,
        prompt=sequence.prompt,
        sampling=sequence.sampling,
    )

    first_user_text = HISTORY_RECALL_MESSAGES[0]
    state = StreamState()
    async with asyncio.timeout(sequence.timeout_seconds):
        await send_initial_user_turn(
            sequence.websocket,
            build_start_payload(context, history=history),
            first_user_text,
            sampling=sequence.sampling,
        )
        reply = await _collect_response(sequence.websocket, state)

    _print_header(sequence.personality, sequence.gender)

    metrics = finalize_metrics(state)
    _print_exchange(1, first_user_text, reply, metrics)
    record_ttfb(sequence.ttfb_samples, metrics)

    for index, user_text in enumerate(HISTORY_RECALL_MESSAGES[1:], 2):
        reply, _ = await _send_message_request(
            sequence,
            context,
            user_text,
            index,
        )


# ============================================================================
# Public API
# ============================================================================


async def run_history_replay(request: HistoryRunRequest) -> None:
    """Run the history recall test."""
    authenticated_url = build_websocket_url(request.server_url, api_key=request.api_key)
    authentication_headers = build_api_key_headers(api_key=request.api_key)
    ttfb_samples = TTFBSamples()
    session_id = f"history-{uuid.uuid4()}"
    prompt = select_prompt(request.gender, request.personality)

    async with connect_websocket(
        authenticated_url,
        headers=authentication_headers,
        ping_interval=DEFAULT_WEBSOCKET_PING_INTERVAL_SECONDS,
        ping_timeout=DEFAULT_WEBSOCKET_PING_TIMEOUT_SECONDS,
    ) as websocket:
        try:
            await _run_history_sequence(
                HistorySequence(
                    websocket=websocket,
                    session_id=session_id,
                    gender=request.gender,
                    personality=request.personality,
                    prompt=prompt,
                    sampling=request.sampling,
                    timeout_seconds=request.timeout_seconds,
                    ttfb_samples=ttfb_samples,
                ),
            )
        finally:
            await send_end_frame(websocket)

    write_line()
    if has_ttfb_samples(ttfb_samples):
        emit_ttfb_summary(ttfb_samples, print)
    else:
        write_line(dim("No TTFB samples collected"))


__all__ = ["HistoryRunRequest", "run_history_replay"]
