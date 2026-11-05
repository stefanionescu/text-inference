"""Message handler builders for cancel test phases.

This module provides factory functions that create message callbacks
for the cancel and recovery phases. Handlers update StreamState as
messages arrive and signal completion when done.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, TypedDict
from functools import partial
from collections.abc import Callable

from tests.harness.client.websocket import finalize_metrics

if TYPE_CHECKING:
    from tests.state import StreamState

EXPECTED_MESSAGE_TYPES = frozenset({"token", "final", "done", "cancelled", "error"})


class DispatchResult(TypedDict, total=False):
    """Completion state returned by cancel-suite dispatch callbacks."""

    is_done: bool
    cancelled: bool
    error: str
    metrics: dict[str, Any]


type DispatchValue = bool | DispatchResult
type MessageCallback = Callable[[dict[str, object]], DispatchValue]


def _message_text(message: dict[str, object], key: str) -> str:
    value = message.get(key, "")
    if isinstance(value, str):
        return value
    return ""


def _record_token(state: StreamState, message: dict[str, object], *, is_first_tracked: bool) -> bool:
    chunk = _message_text(message, "text")
    if not chunk:
        return True
    if is_first_tracked and state.first_token_timestamp is None:
        state.first_token_timestamp = time.perf_counter()
    state.completion_text += chunk
    state.chunks += 1
    return True


def _apply_result_text(state: StreamState, message: dict[str, object]) -> bool:
    normalized = _message_text(message, "normalized_text")
    has_text = bool(normalized)
    if has_text:
        state.completion_text = normalized
    return True


def _cancel_done(_: dict[str, object], *, is_cancelled: bool) -> DispatchResult:
    payload: DispatchResult = {"is_done": True}
    payload["cancelled"] = is_cancelled
    return payload


def _recovery_done(state: StreamState, _: dict[str, object], *, is_cancelled: bool) -> DispatchResult:
    metrics = finalize_metrics(state, is_cancelled=is_cancelled)
    payload: DispatchResult = {"is_done": True, "cancelled": is_cancelled}
    payload["metrics"] = metrics
    return payload


def _handle_error(message: dict[str, object]) -> DispatchResult:
    error_message = message.get("message", "unknown error")
    return {"is_done": True, "error": str(error_message)}


def build_phase_callbacks(state: StreamState, *, is_recovery: bool) -> dict[str, MessageCallback]:
    """Build message callbacks for one phase of the cancel suite.

    The recovery phase runs to completion, so its callbacks track first-token
    timing and report full metrics. The cancel phase is interrupted before
    completion, so its callbacks track basic state only.

    Args:
        state: Mutable stream state to update as messages arrive.
        is_recovery: Whether the callbacks serve the recovery phase.

    Returns:
        Dict mapping message types to handler functions.

    """
    finish: Callable[..., DispatchResult] = partial(_recovery_done, state) if is_recovery else _cancel_done
    callbacks: dict[str, MessageCallback] = {
        "token": partial(_record_token, state, is_first_tracked=is_recovery),
        "final": partial(_apply_result_text, state),
        "done": partial(finish, is_cancelled=False),
        "cancelled": partial(finish, is_cancelled=True),
        "error": _handle_error,
    }
    if callbacks.keys() != EXPECTED_MESSAGE_TYPES:
        raise AssertionError
    return callbacks


__all__ = ["DispatchResult", "MessageCallback", "build_phase_callbacks"]
