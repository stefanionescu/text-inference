"""Data types for the benchmark test suite."""

from __future__ import annotations

from typing import Any
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
    first_3_words_ms: float | None = None

    def to_result(self, *, is_successful: bool, phase: int) -> dict[str, Any]:
        """Convert metrics to a result dict."""
        return {
            "ok": is_successful,
            "phase": phase,
            "ttfb_ms": self.ttfb_ms,
            "first_sentence_ms": self.first_sentence_ms,
            "first_3_words_ms": self.first_3_words_ms,
        }


__all__ = [
    "BenchmarkConfig",
    "TransactionMetrics",
]
