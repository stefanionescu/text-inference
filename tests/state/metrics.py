"""Shared payload types for test utilities."""

from __future__ import annotations

import time
from dataclasses import field, dataclass


@dataclass(frozen=True)
class SessionContext:
    """Immutable context for building session payloads.

    Attributes:
        session_id: ID of the session.
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        prompt: Prompt text.
        sampling: Sampling overrides of the request.

    """

    session_id: str
    gender: str | None
    personality: str | None
    prompt: str | None
    sampling: dict[str, float | int] | None = None


@dataclass
class StreamState:
    """Mutable state for stream metric tracking.

    Attributes:
        sent_timestamp: Time of the sent.
        completion_text: Text of the completion.
        first_token_timestamp: Time of the first token.
        first_sentence_timestamp: Time of the first sentence.
        first_three_words_timestamp: Time of the first three words.
        chunks: Number of chunks that arrived.

    """

    sent_timestamp: float = field(default_factory=time.perf_counter)
    completion_text: str = ""
    first_token_timestamp: float | None = None
    first_sentence_timestamp: float | None = None
    first_three_words_timestamp: float | None = None
    chunks: int = 0


@dataclass
class TTFBSamples:
    """Accumulated TTFB and latency samples.

    Attributes:
        samples: Latency samples.
        first_three_words_samples: Samples of first three words.
        first_sentence_samples: Samples of first sentence.

    """

    samples: list[float] = field(default_factory=list)
    first_three_words_samples: list[float] = field(default_factory=list)
    first_sentence_samples: list[float] = field(default_factory=list)


@dataclass
class BenchmarkMetrics:
    """Result payload for a single benchmark transaction.

    Attributes:
        is_successful: Whether it is successful.
        phase: Number of the test phase.
        error: Error text or error object to report.
        error_code: Code of the error.
        is_recoverable: Whether it is recoverable.
        ttfb_ms: First-byte time in milliseconds.
        first_sentence_ms: First sentence in milliseconds.
        first_three_words_ms: First three words in milliseconds.

    """

    is_successful: bool
    phase: int = 1
    error: str | None = None
    error_code: str | None = None
    is_recoverable: bool = False
    ttfb_ms: float | None = None
    first_sentence_ms: float | None = None
    first_three_words_ms: float | None = None


__all__ = [
    "BenchmarkMetrics",
    "SessionContext",
    "StreamState",
    "TTFBSamples",
]
