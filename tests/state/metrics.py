"""Shared payload types for test utilities."""

from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SessionContext:
    """Immutable context for building session payloads."""

    session_id: str
    gender: str | None
    personality: str | None
    prompt: str | None
    sampling: dict[str, float | int] | None = None


@dataclass
class StreamState:
    """Mutable state for stream metric tracking."""

    sent_timestamp: float = field(default_factory=time.perf_counter)
    completion_text: str = ""
    first_token_timestamp: float | None = None
    first_sentence_timestamp: float | None = None
    first_three_words_timestamp: float | None = None
    chunks: int = 0


@dataclass
class TTFBSamples:
    """Accumulated TTFB and latency samples."""

    samples: list[float] = field(default_factory=list)
    first_three_words_samples: list[float] = field(default_factory=list)
    first_sentence_samples: list[float] = field(default_factory=list)


@dataclass
class BenchmarkMetrics:
    """Result payload for a single benchmark transaction."""

    is_successful: bool
    phase: int = 1
    error: str | None = None
    error_code: str | None = None
    is_recoverable: bool = False
    ttfb_ms: float | None = None
    first_sentence_ms: float | None = None
    first_3_words_ms: float | None = None


__all__ = [
    "BenchmarkMetrics",
    "SessionContext",
    "StreamState",
    "TTFBSamples",
]
