"""Unit tests for limits configuration derivation and environment behavior."""

from __future__ import annotations

from src.runtime.limits import read_limit_settings


def test_limits_context_length() -> None:
    """Test the context length is the sum of every prompt budget."""
    prompt_tokens = 10
    history_tokens = 20
    user_tokens = 30
    context_buffer = 40
    limit_values = read_limit_settings(
        environment={
            "PROMPT_MAX_TOKENS": str(prompt_tokens),
            "HISTORY_MAX_TOKENS": str(history_tokens),
            "USER_UTTERANCE_MAX_TOKENS": str(user_tokens),
            "CONTEXT_BUFFER": str(context_buffer),
        },
    )

    assert limit_values["MAXIMUM_CONTEXT_LENGTH"] == prompt_tokens + history_tokens + user_tokens + context_buffer


def test_limits_trim_target() -> None:
    """Test the history trim target applies the configured retention percentage."""
    history_tokens = 3000
    retention_percentage = 50
    limit_values = read_limit_settings(
        environment={
            "HISTORY_MAX_TOKENS": str(history_tokens),
            "HISTORY_RETENTION_PERCENTAGE": str(retention_percentage),
        },
    )

    assert limit_values["TRIMMED_HISTORY_LENGTH"] == history_tokens * retention_percentage // 100
