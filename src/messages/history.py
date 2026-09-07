"""Shared history parsing helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from src.session.parsing import parse_history_messages

if TYPE_CHECKING:
    from collections.abc import Mapping
    from src.session.runtime import SessionRuntime
    from src.state.session import HistoryMessage, SessionState


def _history_turn_count(state: SessionState) -> int:
    """Return the number of stored history messages."""
    if state.history_messages is not None:
        return len(state.history_messages)
    return 0


def history_messages(
    session_runtime: SessionRuntime,
    state: SessionState,
    message: Mapping[str, object],
) -> list[HistoryMessage]:
    """Resolve and trim a client history payload into runtime state."""
    if _history_turn_count(state) > 0:
        return session_runtime.history.get_messages(state)

    history_messages = message.get("history")
    if not isinstance(history_messages, list):
        return session_runtime.history.get_messages(state)

    history_messages = parse_history_messages(cast("list[object]", history_messages))
    session_runtime.history.set_mode_histories(state, history_messages=history_messages)
    return session_runtime.history.get_messages(state)


__all__ = ["history_messages"]
