"""WebSocket message parsing and dispatch utilities.

This module provides helpers for parsing JSON messages from WebSocket frames
and dispatching them to type-specific callbacks. It supports both sync and
async callbacks and gracefully handles malformed JSON.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast
import inspect

from tests.harness.client.errors import StreamError, MessageParseError

from .payloads import build_message_payload
from .connection import receive_raw_frame

if TYPE_CHECKING:
    from collections.abc import Mapping, Callable, Awaitable, AsyncIterator


async def _send_json_frame(websocket: object, payload: dict[str, object]) -> None:
    serialized_payload = json.dumps(payload)
    sender = getattr(websocket, "send_text", None)
    if not callable(sender):
        sender = getattr(websocket, "send", None)
    if not callable(sender):
        message = "websocket-like object must expose send_text() or send()"
        raise TypeError(message)
    send = cast("Callable[[str], object]", sender)
    result = send(serialized_payload)
    if inspect.isawaitable(result):
        await result


def parse_message(raw_frame: str) -> dict[str, object]:
    """Parse a raw WebSocket frame into a JSON dict.

    Args:
        raw_frame: Unvalidated frame as received.

    Returns:
        A JSON dict.

    Raises:
        MessageParseError: Invalid JSON frame: `raw_frame`.

    """
    try:
        message = json.loads(raw_frame)
    except json.JSONDecodeError as exception:
        error_message = f"Invalid JSON frame: {raw_frame!r}"
        raise MessageParseError(error_message) from exception
    if not isinstance(message, dict):
        error_message = f"Expected JSON object frame: {raw_frame!r}"
        raise MessageParseError(error_message)
    mapping = cast("dict[object, object]", message)
    if any(not isinstance(key, str) for key in mapping):
        error_message = f"Expected string JSON object keys: {raw_frame!r}"
        raise MessageParseError(error_message)
    return cast("dict[str, object]", message)


def message_text(
    message: dict[str, object],
    key: str,
    *,
    default: str | None = None,
) -> str | None:
    """Return one optional string frame member.

    Args:
        message: Message to send, check, or report.
        key: Lookup key.
        default: Value to use when the setting is absent.

    Returns:
        One optional string frame member.

    Raises:
        TypeError: Websocket frame `key` must be a string.

    """
    value = message.get(key, default)
    if value is None:
        return None
    if not isinstance(value, str):
        error_message = f"websocket frame {key} must be a string"
        raise TypeError(error_message)
    return value


async def iter_messages(
    websocket: object,
    *,
    receive_timeout_seconds: float | None = None,
    is_invalid_ignored: bool = True,
) -> AsyncIterator[dict[str, object]]:
    """Yield parsed JSON messages from a websocket connection.

    Args:
        websocket: WebSocket connection (websockets client or Starlette test client).
        receive_timeout_seconds: Optional timeout applied to each recv call.
        is_invalid_ignored: Whether malformed frames are silently skipped.

    Yields:
        Parsed JSON messages from a websocket connection.

    Raises:
        MessageParseError: The operation fails with this error.

    """
    while True:
        raw_frame = await receive_raw_frame(websocket, receive_timeout_seconds=receive_timeout_seconds)
        try:
            yield parse_message(raw_frame)
        except MessageParseError:
            if is_invalid_ignored:
                continue
            raise


async def bootstrap_session(
    websocket: object,
    start_payload: dict[str, object],
) -> None:
    """Send a bootstrap-only start payload and wait for the terminal done frame.

    Args:
        websocket: WebSocket connection of the client.
        start_payload: Start payload.

    Raises:
        RuntimeError: Unexpected websocket frame during bootstrap: `message`.
        StreamError: The operation fails with this error.

    """
    await _send_json_frame(websocket, start_payload)
    async for message in iter_messages(websocket):
        message_type = message.get("type")
        if message_type == "done":
            return
        if message_type == "error":
            raise StreamError(message)
        error_message = f"Unexpected websocket frame during bootstrap: {message!r}"
        raise RuntimeError(error_message)
    error_message = "WebSocket closed before bootstrap completed"
    raise RuntimeError(error_message)


async def send_initial_user_turn(
    websocket: object,
    start_payload: dict[str, object],
    user_text: str,
    *,
    sampling: dict[str, float | int | bool] | None = None,
) -> None:
    """Bootstrap a session, then send the first real user message.

    Args:
        websocket: WebSocket connection of the client.
        start_payload: Start payload.
        user_text: Text of the user.
        sampling: Sampling overrides of the request.

    """
    message_payload = build_message_payload(user_text, sampling=sampling)
    await bootstrap_session(websocket, start_payload)
    await _send_json_frame(websocket, message_payload)


async def dispatch_message[ResultT](
    message: dict[str, object],
    callbacks: Mapping[str, Callable[[dict[str, object]], Awaitable[ResultT] | ResultT]],
    *,
    default: Callable[[dict[str, object]], Awaitable[ResultT] | ResultT] | None = None,
) -> ResultT | None:
    """Dispatch a websocket message to a callback based on its `type` field.

    Callbacks can be synchronous or asynchronous callables.

    Args:
        message: Message to send, check, or report.
        callbacks: Callback for each server message type.
        default: Value to use when the setting is absent.

    Returns:
        The result t.

    """
    message_type = message.get("type")
    message_callback = callbacks.get(message_type) if isinstance(message_type, str) else None
    if message_callback is None:
        message_callback = default
    if message_callback is None:
        return None

    result = message_callback(message)
    if inspect.isawaitable(result):
        return await result
    return result


__all__ = [
    "MessageParseError",
    "bootstrap_session",
    "dispatch_message",
    "iter_messages",
    "message_text",
    "parse_message",
    "send_initial_user_turn",
]
