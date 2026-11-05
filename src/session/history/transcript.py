"""Render and trim the session history transcript."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.session.history.turns import group_turns, flatten_turns

if TYPE_CHECKING:
    from collections.abc import Callable

    from src.session.state import SessionState, HistoryMessage
    from src.runtime.config import HistorySettings
    from src.tokens.tokenizer import ThreadSafeTokenizer


def _trim_oldest_turns(
    turns: list[list[HistoryMessage]],
    *,
    target_tokens: int,
    count_turn_tokens: Callable[[list[list[HistoryMessage]]], int],
) -> list[list[HistoryMessage]]:
    """Drop oldest turns until their token count reaches the target.

    Args:
        turns: Conversation turns.
        target_tokens: Token count of the target.
        count_turn_tokens: Function that counts the tokens of a turn.

    Returns:
        The updated value.

    """
    total_tokens = count_turn_tokens(turns)
    if total_tokens <= target_tokens:
        return turns

    tokens_to_remove = total_tokens - target_tokens
    average_tokens_per_turn = total_tokens // len(turns)
    estimated_removals = max(1, tokens_to_remove // max(1, average_tokens_per_turn))
    removal_count = min(estimated_removals, len(turns) - 1)
    retained_turns = turns[removal_count:] if removal_count > 0 else turns

    total_tokens = count_turn_tokens(retained_turns)
    while len(retained_turns) > 1 and total_tokens > target_tokens:
        retained_turns.pop(0)
        total_tokens = count_turn_tokens(retained_turns)
    return retained_turns


def format_history(messages: list[HistoryMessage] | None) -> str:
    """Render stored history as a role-labelled transcript.

    Args:
        messages: Messages of the conversation.

    Returns:
        Stored history as a role-labelled transcript.

    """
    if not messages:
        return ""
    chunks = [f"{message.role.title()}: {message.content.strip()}" for message in messages if message.content.strip()]
    return "\n\n".join(chunks)


def trim_history(
    state: SessionState,
    *,
    config: HistorySettings,
    tokenizer: ThreadSafeTokenizer,
    trigger_tokens: int | None = None,
    target_tokens: int | None = None,
) -> None:
    """Trim stored messages when the transcript exceeds the trigger threshold.

    Args:
        state: State of the session or test run.
        config: Settings for this run.
        tokenizer: Tokenizer to use.
        trigger_tokens: Token count of the trigger.
        target_tokens: Token count of the target.

    """
    messages = state.history_messages
    if not messages:
        return
    turns = group_turns(messages)
    if not turns:
        state.history_messages = []
        return

    effective_trigger = int(trigger_tokens) if trigger_tokens is not None else config.trigger_tokens
    effective_target = int(target_tokens) if target_tokens is not None else config.target_tokens
    effective_trigger = max(1, effective_trigger)
    effective_target = max(1, min(effective_target, effective_trigger))

    def _count(candidate_turns: list[list[HistoryMessage]]) -> int:
        """Count tokens in grouped history turns.

        Args:
            candidate_turns: Candidate turns.

        Returns:
            Tokens in grouped history turns.

        """
        return tokenizer.count(format_history(flatten_turns(candidate_turns)))

    if _count(turns) <= effective_trigger:
        return
    trimmed_turns = _trim_oldest_turns(
        turns,
        target_tokens=effective_target,
        count_turn_tokens=_count,
    )
    state.history_messages = flatten_turns(trimmed_turns)


__all__ = [
    "format_history",
    "trim_history",
]
