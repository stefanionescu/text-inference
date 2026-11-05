"""Data types for the benchmark test suite."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BenchmarkConfig:
    """Configuration for a benchmark run."""

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
    """Timing metrics for a single benchmark transaction."""

    ttfb_ms: float | None = None
    first_sentence_ms: float | None = None
    first_three_words_ms: float | None = None


__all__ = [
    "BenchmarkConfig",
    "TransactionMetrics",
]
