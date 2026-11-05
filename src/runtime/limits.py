"""Runtime token and connection limit settings."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from collections.abc import Mapping


class LimitSettings(TypedDict):
    """Resolved limit settings with concrete types.

    Attributes:
        PROMPT_MAX_TOKENS: Token count of the prompt max.
        HISTORY_MAX_TOKENS: Token count of the history max.
        USER_UTTERANCE_MAX_TOKENS: Token count of the user utterance max.
        HISTORY_RETENTION_PERCENTAGE: History retention percentage.
        CONTEXT_BUFFER: Context buffer.
        MAXIMUM_CONTEXT_LENGTH: Largest allowed context length.
        TRIMMED_HISTORY_LENGTH: Trimmed history length.
        STREAM_FLUSH_MILLISECONDS: Stream flush in milliseconds.
        MAXIMUM_OUTPUT_TOKENS: Largest allowed output tokens.
        MAX_CONCURRENT_CONNECTIONS: Largest allowed concurrent connections.

    """

    PROMPT_MAX_TOKENS: int
    HISTORY_MAX_TOKENS: int
    USER_UTTERANCE_MAX_TOKENS: int
    HISTORY_RETENTION_PERCENTAGE: int
    CONTEXT_BUFFER: int
    MAXIMUM_CONTEXT_LENGTH: int
    TRIMMED_HISTORY_LENGTH: int
    STREAM_FLUSH_MILLISECONDS: float
    MAXIMUM_OUTPUT_TOKENS: int
    MAX_CONCURRENT_CONNECTIONS: int | None


def _read_environment_value(
    key: str,
    default: str,
    *,
    environment: Mapping[str, str] | None,
) -> str:
    """Resolve one value from an environment mapping or process environment.

    Args:
        key: Lookup key.
        default: Value to use when the setting is absent.
        environment: Environment variables to read.

    Returns:
        One value from an environment mapping or process environment.

    """
    raw_value = os.getenv(key) if environment is None else environment.get(key)
    return default if raw_value is None else raw_value


def read_limit_settings(*, environment: Mapping[str, str] | None = None) -> LimitSettings:
    """Read token and connection limits from environment values.

    Args:
        environment: Environment variables to read.

    Returns:
        Token and connection limits from environment values.

    """
    maximum_prompt_tokens = int(
        _read_environment_value("PROMPT_MAX_TOKENS", "1500", environment=environment),
    )
    history_max_tokens = int(
        _read_environment_value("HISTORY_MAX_TOKENS", "3000", environment=environment),
    )
    maximum_user_utterance_tokens = int(
        _read_environment_value("USER_UTTERANCE_MAX_TOKENS", "500", environment=environment),
    )
    history_retention_percentage = int(
        _read_environment_value("HISTORY_RETENTION_PERCENTAGE", "66", environment=environment),
    )
    context_buffer = int(_read_environment_value("CONTEXT_BUFFER", "25", environment=environment))

    maximum_length = maximum_prompt_tokens + history_max_tokens + maximum_user_utterance_tokens + context_buffer
    trimmed_history_length = history_max_tokens * history_retention_percentage // 100

    stream_flush_milliseconds = float(
        _read_environment_value("STREAM_FLUSH_MILLISECONDS", "0", environment=environment),
    )
    maximum_output_tokens = int(_read_environment_value("MAXIMUM_OUTPUT_TOKENS", "150", environment=environment))

    raw_maximum_connections = _read_environment_value(
        "MAX_CONCURRENT_CONNECTIONS",
        "",
        environment=environment,
    )
    maximum_connections: int | None = int(raw_maximum_connections) if raw_maximum_connections else None

    return {
        "PROMPT_MAX_TOKENS": maximum_prompt_tokens,
        "HISTORY_MAX_TOKENS": history_max_tokens,
        "USER_UTTERANCE_MAX_TOKENS": maximum_user_utterance_tokens,
        "HISTORY_RETENTION_PERCENTAGE": history_retention_percentage,
        "CONTEXT_BUFFER": context_buffer,
        "MAXIMUM_CONTEXT_LENGTH": maximum_length,
        "TRIMMED_HISTORY_LENGTH": trimmed_history_length,
        "STREAM_FLUSH_MILLISECONDS": stream_flush_milliseconds,
        "MAXIMUM_OUTPUT_TOKENS": maximum_output_tokens,
        "MAX_CONCURRENT_CONNECTIONS": maximum_connections,
    }


__all__ = [
    "LimitSettings",
    "read_limit_settings",
]
