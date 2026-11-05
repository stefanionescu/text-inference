"""Unit tests for runtime settings assembly."""

from __future__ import annotations

import pytest

from src.runtime.settings import read_settings


def test_settings_sequence_limits() -> None:
    """Test settings assembly computes complete sequence limits."""
    prompt_tokens = 1200
    history_tokens = 1800
    user_tokens = 400
    context_buffer = 50
    max_output_tokens = 175
    settings = read_settings(
        environment={
            "PROMPT_MAX_TOKENS": str(prompt_tokens),
            "HISTORY_MAX_TOKENS": str(history_tokens),
            "USER_UTTERANCE_MAX_TOKENS": str(user_tokens),
            "CONTEXT_BUFFER": str(context_buffer),
            "MAXIMUM_OUTPUT_TOKENS": str(max_output_tokens),
        },
    )

    assert settings.session.maximum_context_length == prompt_tokens + history_tokens + user_tokens + context_buffer
    assert settings.session.maximum_sequence_length == (
        prompt_tokens + history_tokens + user_tokens + context_buffer + max_output_tokens
    )


@pytest.mark.parametrize("setting_name", ["ENFORCE_EAGER", "LOGS_ENABLED"])
def test_settings_boolean_rejection(setting_name: str) -> None:
    """Test boolean environment settings require an exact binary value.

    Args:
        setting_name: Name of the setting.

    """
    with pytest.raises(ValueError, match=f"{setting_name} must be 0 or 1"):
        read_settings(environment={setting_name: "true"})
