"""Stream processing for conversation exchanges."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
import logging
from collections.abc import Callable, Awaitable

from tests.harness.client.errors import ServerError
from tests.harness.client.websocket import record_token, iter_messages, dispatch_message, finalize_metrics

if TYPE_CHECKING:
    from tests.state import StreamState

logger = logging.getLogger(__name__)

StreamResult = bool | None | dict[str, Any]
_StreamCallback = Callable[[dict[str, Any]], Awaitable[StreamResult] | StreamResult]


# ============================================================================
# Internal Helpers
# ============================================================================


def _log_unknown_exchange_message(message: dict[str, Any], exchange_index: int) -> bool:
    logger.debug("Exchange %02d ignoring message: %s", exchange_index, message)
    return True


def _handle_token(message: dict[str, Any], state: StreamState, exchange_index: int) -> bool:
    _ = exchange_index
    record_token(state, message.get("text", ""))
    return True


def _handle_result(message: dict[str, Any], state: StreamState) -> bool:
    normalized = message.get("normalized_text")
    if normalized:
        state.completion_text = normalized
    return True


def _handle_done(message: dict[str, Any], state: StreamState, exchange_index: int) -> dict[str, Any]:
    _ = message, exchange_index
    metrics = finalize_metrics(state, is_cancelled=False)
    return {"is_done": True, "metrics": metrics}


def _handle_cancelled(_: dict[str, Any], state: StreamState) -> dict[str, Any]:
    metrics = finalize_metrics(state, is_cancelled=True)
    return {"is_done": True, "metrics": metrics}


def _handle_error(message: dict[str, Any]) -> None:
    error = ServerError.decode_message(message)
    raise error


def _build_exchange_callbacks(state: StreamState, exchange_index: int) -> dict[str, _StreamCallback]:
    return {
        "token": lambda message: _handle_token(message, state, exchange_index),
        "final": lambda message: _handle_result(message, state),
        "done": lambda message: _handle_done(message, state, exchange_index),
        "cancelled": lambda message: _handle_cancelled(message, state),
        "error": _handle_error,
    }


# ============================================================================
# Public API
# ============================================================================


async def stream_exchange(
    websocket: object,
    state: StreamState,
    exchange_index: int,
) -> tuple[str, dict[str, Any]]:
    """Stream a single exchange and return the assistant response and metrics."""
    callbacks = _build_exchange_callbacks(state, exchange_index)
    is_done_seen = False
    done_payload: dict[str, Any] | None = None
    async for message in iter_messages(websocket):
        keep_streaming = await dispatch_message(
            message,
            callbacks,
            default=lambda payload: _log_unknown_exchange_message(payload, exchange_index),
        )
        if isinstance(keep_streaming, dict) and keep_streaming.get("is_done"):
            done_payload = keep_streaming
            is_done_seen = True
            break
        if keep_streaming is False:
            is_done_seen = True
            break
    if not is_done_seen:
        error_message = "WebSocket closed before receiving 'done'"
        raise RuntimeError(error_message)
    metrics = done_payload.get("metrics") if done_payload else None
    if metrics is None:
        metrics = finalize_metrics(state, is_cancelled=False)
    return state.completion_text, metrics


__all__ = ["stream_exchange"]
