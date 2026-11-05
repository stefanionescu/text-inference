"""Shared payload types for test utilities."""

from __future__ import annotations

import time
from dataclasses import field, dataclass


@dataclass(frozen=True)
class SessionContext:
    """Immutable context for building session payloads.

    Attributes:
        session_id: Client-side session label; `build_start_payload` does not send it.
        gender: Gender for the start payload; None omits the field.
        personality: Personality for the start payload; None omits the field.
        prompt: Prompt text for the start payload; None omits the field.
        sampling: Sampling overrides for the start payload; None omits the field.

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
        sent_timestamp: `time.perf_counter` reading when the request was sent.
        completion_text: Text accumulated from the stream; a `final` frame can replace it.
        first_token_timestamp: Reading at the first token, or None before it arrives.
        first_sentence_timestamp: Reading at the first complete sentence, or None before it arrives.
        first_three_words_timestamp: Reading at the first three words, or None before they arrive.
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
        samples: First-byte latencies across exchanges.
        first_three_words_samples: Latencies to the first three words across exchanges.
        first_sentence_samples: Latencies to the first complete sentence across exchanges.

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
