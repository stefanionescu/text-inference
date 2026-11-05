"""Warmup test runner for single-request server testing.

This module provides the warmup workflow that connects to the WebSocket
server, sends a single request, streams the response, and reports timing
metrics. Used for quick server health checks and warmup validation.
"""

from __future__ import annotations

import os
import json
import uuid
from typing import TYPE_CHECKING, Any
import asyncio
from dataclasses import dataclass

import websockets

from tests.state import StreamState, SessionContext
from config.tests.defaults import WARMUP_DEFAULT_MESSAGE
from tests.harness.client.errors import ServerError
from tests.harness.client.prompt import select_prompt
from tests.harness.messages.warmup import WARMUP_DEFAULT_MESSAGES
from tests.harness.client.selection import choose_message
from tests.harness.client.websocket import (
    open_websocket,
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
    red,
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
    DEFAULT_SERVER_URL,
    DEFAULT_PERSONALITY,
    DEFAULT_PING_TIMEOUT_SECONDS,
    DEFAULT_PING_INTERVAL_SECONDS,
)
from tests.harness.logic.conversation.stream import stream_exchange

if TYPE_CHECKING:
    import argparse

    from websockets import WebSocketClientProtocol


@dataclass(frozen=True)
class WarmupConfig:
    """Resolved inputs for one warmup run.

    Attributes:
        server_url: Server URL.
        authenticated_websocket_url: Authenticated websocket URL.
        authentication_headers: Authentication headers.
        api_key: Key of the API.
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        sampling_overrides: Sampling overrides.
        is_double_ttfb_enabled: Whether double first-byte time is enabled.
        user_message: User message.
        prompt: Prompt text.
        timeout_seconds: Timeout in seconds.
        transaction_count: Number of transaction items.

    """

    server_url: str
    authenticated_websocket_url: str
    authentication_headers: dict[str, str]
    api_key: str
    gender: str
    personality: str
    sampling_overrides: dict[str, float | int | bool] | None
    is_double_ttfb_enabled: bool
    user_message: str
    prompt: str
    timeout_seconds: float
    transaction_count: int


def _print_server_error_hint(error: ServerError, api_key: str) -> None:
    """Print human-friendly hints for server errors.

    Args:
        error: Error text or error object to report.
        api_key: Key of the API.

    """
    write_line(f"  {red('ERROR')} {error.error_code}: {error.message}")
    if error.error_code == "authentication_failed":
        preview = f"{api_key[:8]}..." if api_key else "missing"
        write_line(dim(f"  HINT: Check your API_KEY (currently: '{preview}')"))
    elif error.error_code == "server_at_capacity":
        write_line(dim("  HINT: Server is busy. Try again later."))
    elif error.is_recoverable():
        write_line(dim(f"  HINT: {error.format_for_user()}"))


async def _stream_exchange(
    websocket: WebSocketClientProtocol,
    state: StreamState,
    api_key: str,
    exchange_index: int,
) -> tuple[str, dict[str, Any]]:
    """Consume a single exchange, returning assistant text and metrics.

    Args:
        websocket: Connection to read the response from.
        state: Metric tracker for this exchange.
        api_key: Key whose preview the error hint can show.
        exchange_index: One-based exchange number.

    Returns:
        Assistant text and metrics; partial values after the server closes the connection.

    Raises:
        ServerError: The server sent an `error` frame; the error and any hint print first.

    """
    try:
        assistant_text, metrics = await stream_exchange(
            websocket,
            state,
            exchange_index,
        )
    except ServerError as error:
        _print_server_error_hint(error, api_key)
        raise
    except (websockets.ConnectionClosedOK, websockets.ConnectionClosedError):
        write_line(dim("  connection closed by server"))
    else:
        return assistant_text, metrics

    return state.completion_text, finalize_metrics(state, is_cancelled=True)


def _print_transaction_result(
    phase: str | None,
    user_message: str,
    assistant_text: str,
    metrics: dict[str, Any],
) -> None:
    """Print formatted transaction result.

    Args:
        phase: Number of the test phase.
        user_message: User message.
        assistant_text: Text of the assistant.
        metrics: Timing metrics of the request.

    """
    if phase:
        write_line(exchange_header(profile=phase.upper()))
    else:
        write_line(exchange_header())

    write_line(f"  {format_user(user_message)}")
    write_line(f"  {format_assistant(assistant_text)}")

    write_line(f"  {format_metrics_inline(metrics)}")
    write_line(exchange_footer())


# ============================================================================
# Public API
# ============================================================================


def _select_config(arguments: argparse.Namespace) -> WarmupConfig:
    server_url = arguments.server or os.getenv("SERVER_URL", DEFAULT_SERVER_URL)
    api_key = arguments.api_key or os.getenv("API_KEY")
    if not api_key:
        message = "API_KEY environment variable is required and must be set before running tests"
        raise ValueError(message)
    gender_variable = os.getenv("GENDER")
    personality_variable = os.getenv("PERSONALITY")
    gender = arguments.gender or gender_variable or DEFAULT_GENDER
    personality = arguments.personality or personality_variable or DEFAULT_PERSONALITY
    sampling_overrides = getattr(arguments, "sampling", None) or None
    is_double_ttfb_enabled = bool(arguments.is_double_ttfb_enabled)

    user_message = choose_message(
        arguments.message,
        default_message=WARMUP_DEFAULT_MESSAGE,
        defaults=WARMUP_DEFAULT_MESSAGES,
    )
    return WarmupConfig(
        server_url=server_url,
        authenticated_websocket_url=build_websocket_url(server_url, api_key=api_key),
        authentication_headers=build_api_key_headers(api_key=api_key),
        api_key=api_key,
        gender=gender,
        personality=personality,
        sampling_overrides=sampling_overrides,
        is_double_ttfb_enabled=is_double_ttfb_enabled,
        user_message=user_message,
        prompt=select_prompt(gender, personality),
        timeout_seconds=float(arguments.timeout),
        transaction_count=2 if is_double_ttfb_enabled else 1,
    )


def _print_header(config: WarmupConfig) -> None:
    test_name = "WARMUP (double-ttfb)" if config.is_double_ttfb_enabled else "WARMUP"
    write_line(f"\n{section_header(test_name)}")
    write_line(dim(f"  server: {config.server_url}"))
    write_line(dim(f"  profile: {config.gender}/{config.personality}\n"))


async def _run_transactions(websocket: WebSocketClientProtocol, config: WarmupConfig) -> None:
    session_id = str(uuid.uuid4())
    context = SessionContext(
        session_id=session_id,
        gender=config.gender,
        personality=config.personality,
        prompt=config.prompt,
        sampling=config.sampling_overrides,
    )
    try:
        for index in range(config.transaction_count):
            phase_label = ("first" if index == 0 else "second") if config.is_double_ttfb_enabled else None
            state = StreamState()
            try:
                async with asyncio.timeout(config.timeout_seconds):
                    if index == 0:
                        await send_initial_user_turn(
                            websocket,
                            build_start_payload(context),
                            config.user_message,
                            sampling=config.sampling_overrides,
                        )
                    else:
                        payload = build_message_payload(config.user_message, sampling=config.sampling_overrides)
                        await websocket.send(json.dumps(payload))
                    assistant_text, metrics = await _stream_exchange(
                        websocket,
                        state,
                        config.api_key,
                        exchange_index=index + 1,
                    )
            except TimeoutError:
                write_line(f"  {red('TIMEOUT')} after {config.timeout_seconds:.1f}s")
                assistant_text = state.completion_text
                metrics = finalize_metrics(state, is_cancelled=True)
            _print_transaction_result(phase_label, config.user_message, assistant_text, metrics)
    finally:
        await send_end_frame(websocket)


async def run_warmup(arguments: argparse.Namespace) -> None:
    """Execute a single warmup request and report metrics.

    Args:
        arguments: Parsed command-line arguments.

    """
    config = _select_config(arguments)
    _print_header(config)

    async with open_websocket(
        lambda: connect_websocket(
            config.authenticated_websocket_url,
            headers=config.authentication_headers,
            max_queue=None,
            ping_interval=DEFAULT_PING_INTERVAL_SECONDS,
            ping_timeout=DEFAULT_PING_TIMEOUT_SECONDS,
        ),
    ) as websocket:
        await _run_transactions(websocket, config)


__all__ = ["run_warmup"]
