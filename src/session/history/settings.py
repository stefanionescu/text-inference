"""Runtime configuration for session history behavior."""

from __future__ import annotations

from src.state.settings import HistorySettings
from config.limits import HISTORY_MAX_TOKENS, TRIMMED_HISTORY_LENGTH


def build_history_runtime_config(
    *,
    trigger_tokens: int = HISTORY_MAX_TOKENS,
    target_tokens: int = TRIMMED_HISTORY_LENGTH,
) -> HistorySettings:
    """Build a normalized history runtime config."""
    return HistorySettings(
        trigger_tokens=max(1, int(trigger_tokens)),
        target_tokens=max(1, int(target_tokens)),
    )


__all__ = ["build_history_runtime_config"]
