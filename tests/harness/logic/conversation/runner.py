"""Conversation history test runner.

This module orchestrates multi-turn conversation tests over WebSocket. It
maintains session state, tracks TTFB metrics across exchanges, and validates
that history retention works correctly under bounded-history constraints.
"""

from __future__ import annotations

import json
import uuid
from typing import TYPE_CHECKING
import asyncio
import logging
from dataclasses import dataclass

from tests.state import StreamState, TTFBSamples, ConversationSession
from tests.harness.metrics import record_ttfb, has_ttfb_samples, emit_ttfb_summary
from tests.harness.client.rate import SlidingWindowPacer
from tests.harness.client.prompt import select_prompt
from tests.harness.client.websocket import (
    send_end_frame,
    connect_websocket,
    build_websocket_url,
    build_api_key_headers,
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
    DEFAULT_GENDER,
    DEFAULT_PERSONALITY,
    DEFAULT_PING_TIMEOUT_SECONDS,
    DEFAULT_PING_INTERVAL_SECONDS,
)
from tests.harness.environment.variables import read_environment_float, read_environment_integer

from .stream import stream_exchange
from .session import build_start_payload, build_message_payload

if TYPE_CHECKING:
    from collections.abc import Sequence

    from websockets import WebSocketClientProtocol

logger = logging.getLogger(__name__)

RATE_LIMIT_WINDOW_SECONDS = read_environment_float("WEBSOCKET_RATE_LIMIT_WINDOW_SECONDS", 60.0)
MAXIMUM_MESSAGES_PER_WINDOW = read_environment_integer("WEBSOCKET_MESSAGES_PER_WINDOW", 20)


@dataclass(frozen=True, slots=True)
class ConversationRunRequest:
    """Inputs for the conversation e2e helper."""

    server_url: str
    api_key: str | None
    prompts: Sequence[str]
    gender: str
    personality: str
    timeout_seconds: float
    sampling: dict[str, float | int | bool] | None


@dataclass(frozen=True, slots=True)
class _ConversationContext:
    session: ConversationSession
    message_pacer: SlidingWindowPacer
    ttfb_samples: TTFBSamples
    timeout_seconds: float


def _build_context(request: ConversationRunRequest, gender: str, personality: str) -> _ConversationContext:
    prompt = select_prompt(gender, personality)
    session = ConversationSession(
        session_id=f"sess-{uuid.uuid4()}",
        gender=gender,
        personality=personality,
        prompt=prompt,
        sampling=request.sampling,
    )
    return _ConversationContext(
        session=session,
        message_pacer=SlidingWindowPacer(MAXIMUM_MESSAGES_PER_WINDOW, RATE_LIMIT_WINDOW_SECONDS),
        ttfb_samples=TTFBSamples(),
        timeout_seconds=request.timeout_seconds,
    )


def _write_conversation_header(session: ConversationSession) -> None:
    write_line(f"\n{section_header('CONVERSATION TEST')}")
    write_line(dim(f"  session: {session.session_id}"))
    write_line(dim(f"  profile: {session.gender}/{session.personality}\n"))


async def _send_turn(
    websocket: WebSocketClientProtocol, context: _ConversationContext, index: int, user_text: str
) -> None:
    await context.message_pacer.wait_turn()
    if index == 1:
        await send_initial_user_turn(
            websocket,
            build_start_payload(context.session),
            user_text,
            sampling=context.session.sampling,
        )
        return
    await websocket.send(json.dumps(build_message_payload(context.session, user_text)))


async def _run_turn(
    websocket: WebSocketClientProtocol, context: _ConversationContext, index: int, user_text: str
) -> None:
    state = StreamState()
    write_line(exchange_header(index=index))
    write_line(f"  {format_user(user_text)}")

    async with asyncio.timeout(context.timeout_seconds):
        await _send_turn(websocket, context, index, user_text)
        assistant_text, metrics = await stream_exchange(websocket, state, index)
    record_ttfb(context.ttfb_samples, metrics)

    write_line(f"  {format_assistant(assistant_text)}")
    write_line(f"  {format_metrics_inline(metrics)}")
    write_line(exchange_footer())


async def _finish_conversation(websocket: WebSocketClientProtocol, context: _ConversationContext) -> None:
    write_line()
    if has_ttfb_samples(context.ttfb_samples):
        emit_ttfb_summary(context.ttfb_samples, print)
    await send_end_frame(websocket)


async def run_conversation(request: ConversationRunRequest) -> None:
    """Execute a multi-turn conversation test."""
    if not request.prompts:
        message = "Conversation prompt list is empty; nothing to send."
        raise ValueError(message)

    gender = request.gender or DEFAULT_GENDER
    personality = request.personality or DEFAULT_PERSONALITY

    authenticated_websocket_url = build_websocket_url(request.server_url, api_key=request.api_key)
    authentication_headers = build_api_key_headers(api_key=request.api_key)
    context = _build_context(request, gender, personality)
    _write_conversation_header(context.session)

    async with connect_websocket(
        authenticated_websocket_url,
        headers=authentication_headers,
        max_queue=None,
        ping_interval=DEFAULT_PING_INTERVAL_SECONDS,
        ping_timeout=DEFAULT_PING_TIMEOUT_SECONDS,
    ) as websocket:
        try:
            for index, user_text in enumerate(request.prompts, start=1):
                await _run_turn(websocket, context, index, user_text)
        finally:
            await _finish_conversation(websocket, context)


__all__ = ["ConversationRunRequest", "run_conversation"]
