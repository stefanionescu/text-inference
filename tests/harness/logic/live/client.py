"""WebSocket client for interactive live sessions.

This module provides the LiveClient class that wraps a WebSocket connection
and provides high-level methods for sending messages and streaming responses.
It handles message parsing, error reporting, and stats logging.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast
import asyncio
import logging
import contextlib

import websockets

from tests.state import LiveSession, StreamState, StreamResult
from tests.harness.client.errors import ServerError, TestClientError, IdleTimeoutError, ConnectionClosedError
from tests.harness.client.websocket import (
    message_text,
    iter_messages,
    send_end_frame,
    finalize_metrics,
    send_initial_user_turn,
)
from tests.harness.reporting.terminal import dim, cyan, write_line, write_text, format_metrics_inline

from .stream import _StreamContext
from .session import build_start_payload, build_message_payload

if TYPE_CHECKING:
    from websockets import WebSocketClientProtocol

logger = logging.getLogger("live")


def _log_server_error(message: dict[str, object]) -> None:
    """Log a server error message."""
    error_code = message.get("error_code") or message.get("code")
    status = message.get("status")
    server_message = message.get("message")
    logger.error(
        "Server error code=%s status=%s message=%s",
        error_code,
        status,
        server_message,
    )


# ============================================================================
# Public API
# ============================================================================


class LiveClient:
    """High-level WebSocket client for interactive sessions."""

    def __init__(self, websocket: object, session: LiveSession, transaction_timeout_seconds: float) -> None:
        """Initialize a live client around an open WebSocket."""
        self.websocket: WebSocketClientProtocol = cast("WebSocketClientProtocol", websocket)
        self.session = session
        self.transaction_timeout_seconds = transaction_timeout_seconds
        self._is_closed = False
        self.is_stats_logging_enabled = False
        self._close_task: asyncio.Task[None] | None = None

    async def send_user_message(self, text: str) -> StreamResult:
        """Send a user message and return the result with assistant's response."""
        async with asyncio.timeout(self.transaction_timeout_seconds):
            return await self._send_user_message(text)

    async def _send_user_message(self, text: str) -> StreamResult:
        """Send and consume one complete live turn."""
        if not self.session.is_started:
            await send_initial_user_turn(
                self.websocket,
                build_start_payload(self.session),
                text,
                sampling=self.session.sampling,
            )
            self.session.is_started = True
        else:
            await self._send_payload(build_message_payload(self.session, text))
        state = StreamState()
        result = await self._stream_response(state, is_user_prompt_printed=False)
        if result.is_successful:
            self.session.history.append({"role": "user", "content": text})
            self.session.history.append({"role": "assistant", "content": result.text})
        return result

    async def close(self) -> None:
        """Close the WebSocket connection gracefully."""
        if self._is_closed:
            return
        self._is_closed = True
        try:
            await send_end_frame(self.websocket)
        except asyncio.CancelledError:
            raise
        except Exception as exception:  # noqa: BLE001 # reason: live harness boundary converts client failures to results.
            logger.warning("Failed to send client end frame: %s", exception)
        with contextlib.suppress(Exception):
            await self.websocket.close(code=1000)
            await asyncio.wait_for(self.websocket.wait_closed(), timeout=3.0)

    async def _send_payload(self, payload: dict[str, object]) -> None:
        serialized_payload = json.dumps(payload)
        if not serialized_payload:
            serialized_payload = "{}"
        try:
            await self.websocket.send(serialized_payload)
        except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as exception:
            message = "WebSocket closed while sending payload"
            raise ConnectionClosedError(message) from exception

    async def _stream_response(self, state: StreamState, *, is_user_prompt_printed: bool = True) -> StreamResult:
        """Stream and process the server response."""
        context = _StreamContext(state)
        try:
            async for message in iter_messages(self.websocket):
                result = self._handle_stream_message(message, context, is_user_prompt_printed=is_user_prompt_printed)
                if result is not None:
                    return result
        except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as exception:
            close_code = getattr(exception, "code", None)
            close_reason = getattr(exception, "reason", None)
            if IdleTimeoutError.matches(close_code, close_reason):
                logger.info("Server closed due to idle timeout")
                raise IdleTimeoutError(close_code=close_code, close_reason=close_reason) from exception
            logger.info("Server closed the WebSocket (code=%s)", close_code)
            self._close_task = asyncio.create_task(self.close())
            return StreamResult(text=state.completion_text, is_successful=True)
        error_message = "WebSocket closed before receiving 'done'"
        raise TestClientError(error_message)

    def _handle_stream_message(
        self,
        message: dict[str, object],
        context: _StreamContext,
        *,
        is_user_prompt_printed: bool,
    ) -> StreamResult | None:
        """Handle one server stream frame."""
        message_type = message.get("type")
        result: StreamResult | None = None
        if message_type == "token":
            context.handle_token(message_text(message, "text", default="") or "")
        elif message_type == "final":
            if normalized := message_text(message, "normalized_text"):
                context.state.completion_text = normalized
        elif message_type == "done":
            result = self._handle_done_frame(context, is_user_prompt_printed=is_user_prompt_printed)
        elif message_type == "cancelled":
            result = self._handle_cancelled_frame(context, is_user_prompt_printed=is_user_prompt_printed)
        elif message_type == "error":
            result = self._handle_error_frame(message, context)
        else:
            logger.debug("Ignoring message type=%s payload=%s", message_type, message)
        return result

    def _handle_done_frame(self, context: _StreamContext, *, is_user_prompt_printed: bool) -> StreamResult:
        context.printer.finish()
        if self.is_stats_logging_enabled:
            metrics = finalize_metrics(context.state, is_cancelled=False)
            write_line(dim(f"     {format_metrics_inline(metrics)}"))
            write_line()
        if is_user_prompt_printed:
            write_text(f"{cyan('USER')} ", is_flush_requested=True)
        return StreamResult(text=context.state.completion_text, is_successful=True, is_cancelled=False)

    def _handle_cancelled_frame(
        self,
        context: _StreamContext,
        *,
        is_user_prompt_printed: bool,
    ) -> StreamResult:
        context.printer.finish()
        if self.is_stats_logging_enabled:
            metrics = finalize_metrics(context.state, is_cancelled=True)
            write_line(dim(f"     {format_metrics_inline(metrics)}"))
            write_line()
        if is_user_prompt_printed:
            write_text(f"{cyan('USER')} ", is_flush_requested=True)
        return StreamResult(text=context.state.completion_text, is_successful=True, is_cancelled=True)

    def _handle_error_frame(self, message: dict[str, object], context: _StreamContext) -> StreamResult:
        """Handle an error message frame."""
        context.printer.finish()
        error = ServerError.decode_message(message)
        _log_server_error(message)
        if error.is_recoverable():
            return StreamResult(text=context.state.completion_text, is_successful=False, error=error)
        raise error


__all__ = ["LiveClient"]
