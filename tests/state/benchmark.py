"""Data types for the benchmark test suite."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for a benchmark run.

    Attributes:
        server_url: Server URL.
        api_key: Key of the API.
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        prompt: Prompt text.
        message: Message to send, check, or report.
        timeout_seconds: Timeout in seconds.
        sampling: Sampling overrides of the request.
        is_double_ttfb_enabled: Whether double first-byte time is enabled.

    """

    server_url: str
    api_key: str | None
    gender: str | None
    personality: str | None
    prompt: str | None
    message: str
    timeout_seconds: float
    sampling: dict[str, float | int | bool] | None
    is_double_ttfb_enabled: bool


@dataclass
class TransactionMetrics:
    """Timing metrics for a single benchmark transaction.

    Attributes:
        ttfb_ms: First-byte time in milliseconds.
        first_sentence_ms: First sentence in milliseconds.
        first_three_words_ms: First three words in milliseconds.

    """

    ttfb_ms: float | None = None
    first_sentence_ms: float | None = None
    first_three_words_ms: float | None = None


__all__ = [
    "BenchmarkConfig",
    "TransactionMetrics",
]
