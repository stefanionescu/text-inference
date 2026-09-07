"""Streaming controller - engine agnostic.

This module provides the StreamController, which handles the mechanics
of streaming text generation from any engine implementing the runtime engine
protocol.

Key Features:

1. Engine Abstraction:
   - Works with both vLLM and TensorRT-LLM
   - Uses a pre-initialized engine instance

2. Micro-Buffering:
   - Accumulates small chunks for flush_milliseconds duration
   - Reduces WebSocket message overhead
   - Configurable via flush_milliseconds (0 = no buffering)

3. Timeout Handling:
   - Generation timeout with async context manager
   - Automatic request abortion on timeout
   - TimeoutError propagation for caller handling

4. Cancellation Support:
   - Cooperative cancellation via cancel_check callback
   - StreamCancelledError for clean termination
   - Automatic request abortion on cancel

5. Telemetry:
   - TTFB (Time To First Byte) tracking
   - Total generation time logging
   - Per-request logging with session/request IDs

Works with both vLLM and TensorRT-LLM engines through one structural interface.
"""

from __future__ import annotations

import math
import time
import asyncio
import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass
from src.errors import StreamCancelledError
from src.telemetry.sentry import capture_error
from collections.abc import Awaitable, Callable
from config.runtime.logging import STREAM_LABEL
from src.telemetry.traces import generation_span
from src.telemetry.instruments import get_metrics
from config.runtime.numerics import FLOAT_ZERO_ABS_TOL
from src.telemetry.error_classification import classify_error

if TYPE_CHECKING:
    from src.engines.protocol import Engine, EngineOutput
    from collections.abc import AsyncGenerator, AsyncIterator

logger = logging.getLogger(__name__)


CancelCheck = Callable[[], bool | Awaitable[bool]] | None
CompletionCounter = Callable[[str], int]


@dataclass(slots=True)
class StreamConfig:
    """Configuration for streaming."""

    session_id: str
    request_id: str
    prompt: str
    sampling_parameters: object
    engine: Engine
    timeout_seconds: float
    count_completion_tokens: CompletionCounter
    flush_milliseconds: float = 0.0
    cancellation_check: CancelCheck = None


class StreamController:
    """Handles buffering, cancellation, and logging for generations.

    This controller provides a clean async iterator interface over engine
    generation streams, adding:
    - Micro-buffering for reduced message overhead
    - Timeout enforcement with automatic abortion
    - Cancellation support via callback
    - TTFB and completion telemetry

    Works with any engine implementing the runtime engine protocol,
    including both vLLM and TensorRT-LLM.

    Usage:
        config = StreamConfig(...)
        controller = StreamController(config)
        async for chunk in controller:
            process(chunk)
    """

    def __init__(self, config: StreamConfig) -> None:
        """Initialize stream controller state."""
        self._config = config
        self._full_text: str = ""  # Cumulative generated text
        self._first_byte_latency_milliseconds: float | None = None
        self._is_cancelled = False
        self._buffer: list[str] = []  # Micro-buffering accumulator
        self._last_flush_at = time.perf_counter()  # Last buffer flush time
        self._start_time: float | None = None  # Stream start time

    def __aiter__(self) -> AsyncIterator[str]:
        """Enable async iteration: `async for chunk in controller`."""
        return self.iter_text()

    def _log_stream_start(self) -> float:
        """Log stream start and return the monotonic start time."""
        start = time.perf_counter()
        config = self._config
        self._start_time = start
        logger.info(
            "%s_stream: start session_id=%s request_id=%s timeout_seconds=%.2f flush_milliseconds=%.1f",
            STREAM_LABEL,
            config.session_id,
            config.request_id,
            config.timeout_seconds,
            config.flush_milliseconds,
        )
        return start

    async def _iter_emitted_chunks(self) -> AsyncGenerator[str, None]:
        """Yield buffered chunks produced from engine deltas."""
        async for output in _stream_timed(self._config):
            delta = self._extract_delta(output)
            if not delta:
                continue
            for chunk in self._emit(delta):
                yield chunk

    def _log_cancelled(self) -> None:
        """Log stream cancellation for the current request."""
        config = self._config
        message = "%s_stream: cancelled session_id=%s request_id=%s"
        logger.info(
            message,
            STREAM_LABEL,
            config.session_id,
            config.request_id,
        )

    def _log_timeout(self) -> None:
        """Log stream timeout for the current request."""
        config = self._config
        message = "%s_stream: timeout session_id=%s request_id=%s"
        logger.warning(
            message,
            STREAM_LABEL,
            config.session_id,
            config.request_id,
        )

    def _log_stream_end(self, start: float) -> None:
        """Log stream completion with elapsed time and output length."""
        elapsed_milliseconds = (time.perf_counter() - start) * 1000.0
        config = self._config
        logger.info(
            "%s_stream: end session_id=%s request_id=%s total_length=%s milliseconds=%.1f",
            STREAM_LABEL,
            config.session_id,
            config.request_id,
            len(self._full_text),
            elapsed_milliseconds,
        )

    def _completion_token_count(self) -> int:
        """Return the exact completion token count."""
        return max(0, int(self._config.count_completion_tokens(self._full_text)))

    async def iter_text(self) -> AsyncGenerator[str, None]:
        """Stream text with buffering, timeout, and cancellation.

        Yields:
            Text chunks (possibly buffered based on flush_milliseconds).

        Raises:
            asyncio.TimeoutError: If generation exceeds timeout_seconds.
            StreamCancelledError: If cancel_check returns True.

        """
        metrics = get_metrics()
        metrics.active_generations.add(1)
        start = self._log_stream_start()
        try:
            async for chunk in self._iter_generation_chunks(start):
                yield chunk
        except StreamCancelledError:
            self._is_cancelled = True
            if self._first_byte_latency_milliseconds is None:
                metrics.early_cancel_total.add(1)
            self._log_cancelled()
        except TimeoutError:
            metrics.errors_total.add(1, {"error.type": "generation_timeout"})
            metrics.phase_errors_total.add(1, {"phase": "generation", "error.type": "generation_timeout"})
            self._log_timeout()
            raise
        except Exception as exception:
            capture_error(exception)
            error_type = classify_error(exception)
            metrics.errors_total.add(1, {"error.type": error_type})
            metrics.phase_errors_total.add(1, {"phase": "generation", "error.type": error_type})
            raise
        finally:
            tail = self._finalize_generation(start)
            if tail:
                yield tail

    async def _iter_generation_chunks(self, start: float) -> AsyncGenerator[str, None]:
        """Yield chunks while recording generation span metadata."""
        metrics = get_metrics()
        last_emit = start
        with generation_span(engine_type=type(self._config.engine).__name__) as generation_trace_span:
            async for chunk in self._iter_emitted_chunks():
                now = time.perf_counter()
                if now - last_emit > 0:
                    metrics.token_latency.record(now - last_emit)
                last_emit = now
                yield chunk
            generation_trace_span.set_attribute("completion_tokens", self._completion_token_count())
            generation_trace_span.set_attribute("finish_reason", "complete")

    def _finalize_generation(self, start: float) -> str:
        """Record final stream metrics and return any buffered tail."""
        metrics = get_metrics()
        metrics.active_generations.add(-1)
        elapsed = time.perf_counter() - start
        metrics.request_latency.record(elapsed)
        metrics.phase_latency.record(max(0.0, elapsed), {"phase": "generation"})
        completion_tokens = self._completion_token_count()
        metrics.completion_tokens.record(completion_tokens)
        if completion_tokens > 0:
            metrics.tokens_generated_total.add(completion_tokens)
        tail = "" if self._is_cancelled else self._flush_tail()
        self._log_stream_end(start)
        return tail

    def _extract_delta(self, output: EngineOutput) -> str:
        """Extract new text from the cumulative engine output."""
        text = output.text
        delta = text if not text.startswith(self._full_text) else text[len(self._full_text) :]
        if not delta:
            return ""
        self._full_text = text
        if self._first_byte_latency_milliseconds is None:
            self._first_byte_latency_milliseconds = 0.0
        return delta

    def _emit(self, delta: str) -> list[str]:
        """Buffer or emit a generation delta according to flush settings."""
        config = self._config
        if config.flush_milliseconds <= 0:
            self._record_ttfb()
            return [delta]

        self._buffer.append(delta)
        now = time.perf_counter()
        is_flush_needed = (now - self._last_flush_at) * 1000.0 >= config.flush_milliseconds
        if not is_flush_needed:
            return []

        chunk = "".join(self._buffer)
        self._buffer.clear()
        self._last_flush_at = now
        self._record_ttfb()
        return [chunk]

    def _flush_tail(self) -> str:
        """Return any buffered text that was not flushed during streaming."""
        if self._config.flush_milliseconds <= 0 or not self._buffer:
            return ""
        chunk = "".join(self._buffer)
        self._buffer.clear()
        return chunk

    def _record_ttfb(self) -> None:
        """Record time to first byte once the first chunk is emitted."""
        if self._first_byte_latency_milliseconds is None:
            return
        if not math.isclose(
            self._first_byte_latency_milliseconds,
            0.0,
            rel_tol=0.0,
            abs_tol=FLOAT_ZERO_ABS_TOL,
        ):
            return
        if self._start_time is None:
            return
        self._first_byte_latency_milliseconds = (time.perf_counter() - self._start_time) * 1000.0
        get_metrics().ttft.record(self._first_byte_latency_milliseconds / 1000.0)
        config = self._config
        logger.info(
            "%s_stream: first output session_id=%s request_id=%s ttfb_ms=%.1f",
            STREAM_LABEL,
            config.session_id,
            config.request_id,
            self._first_byte_latency_milliseconds,
        )


async def _stream_timed(
    request: StreamConfig,
) -> AsyncGenerator[EngineOutput, None]:
    """Stream generation with timeout and cancellation support."""
    stream = request.engine.generate_stream(
        prompt=request.prompt,
        sampling_parameters=request.sampling_parameters,
        request_id=request.request_id,
    )
    try:
        async with asyncio.timeout(request.timeout_seconds):
            async for out in stream:
                if await _is_cancellation_requested(request.cancellation_check):
                    get_metrics().engine_abort_retryable_total.add(1, {"reason": "cancelled"})
                    await request.engine.abort(request.request_id)
                    raise StreamCancelledError
                yield out
    except TimeoutError:
        get_metrics().engine_abort_retryable_total.add(1, {"reason": "timeout"})
        await request.engine.abort(request.request_id)
        raise


async def _is_cancellation_requested(cancellation_check: CancelCheck) -> bool:
    """Return whether the optional cancellation callback has fired."""
    if cancellation_check is None:
        return False
    result = cancellation_check()
    if asyncio.iscoroutine(result):
        result = await result
    return bool(result)


__all__ = [
    "StreamCancelledError",
    "StreamConfig",
    "StreamController",
]
