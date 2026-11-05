"""Pure helpers for working with stored history as whole turns."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.session.state import HistoryMessage

if TYPE_CHECKING:
    from collections.abc import Sequence


def copy_messages(messages: Sequence[HistoryMessage]) -> list[HistoryMessage]:
    """Return normalized copies of non-empty messages.

    Args:
        messages: Messages of the conversation.

    Returns:
        Normalized copies of non-empty messages.

    """
    copied: list[HistoryMessage] = []
    for message in messages:
        content = (message.content or "").strip()
        if not content:
            continue
        copied.append(HistoryMessage(role=message.role, content=content))
    return copied


def group_turns(messages: Sequence[HistoryMessage]) -> list[list[HistoryMessage]]:
    """Group messages into trim-safe turns.

    A turn starts with a user message and keeps any following assistant
    messages until the next user. Leading assistant-only messages are grouped
    together so trimming can still drop them as a unit.

    Args:
        messages: Messages of the conversation.

    Returns:
        Messages into trim-safe turns.

    """
    turns: list[list[HistoryMessage]] = []
    current_turn: list[HistoryMessage] | None = None
    leading_assistants: list[HistoryMessage] = []

    for message in copy_messages(messages):
        if message.role == "user":
            if leading_assistants:
                turns.append(leading_assistants)
                leading_assistants = []
            if current_turn is not None:
                turns.append(current_turn)
            current_turn = [message]
            continue

        if current_turn is None:
            leading_assistants.append(message)
            continue

        current_turn.append(message)

    if leading_assistants:
        turns.append(leading_assistants)
    if current_turn is not None:
        turns.append(current_turn)

    return turns


def flatten_turns(turns: Sequence[Sequence[HistoryMessage]]) -> list[HistoryMessage]:
    """Flatten grouped turns back into normalized messages.

    Args:
        turns: Conversation turns.

    Returns:
        Grouped turns back into normalized messages.

    """
    return copy_messages([message for turn in turns for message in turn])


__all__ = [
    "copy_messages",
    "flatten_turns",
    "group_turns",
]
