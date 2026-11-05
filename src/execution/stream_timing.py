"""Stream settings, and the timeout and cancellation guard around an engine stream."""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
from dataclasses import dataclass
from collections.abc import Callable, Awaitable

from src.errors import StreamCancelledError
from src.telemetry.instruments import get_metrics

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from src.engines.protocol import Engine, EngineOutput


CancelCheck = Callable[[], bool | Awaitable[bool]] | None
CompletionCounter = Callable[[str], int]


@dataclass(slots=True)
class StreamConfig:
    """Configuration for streaming.

    Attributes:
        session_id: ID of the session.
        request_id: ID of the request.
        prompt: Prompt text.
        sampling_parameters: Sampling parameters.
        engine: Inference engine that serves the request.
        timeout_seconds: Timeout in seconds.
        count_completion_tokens: Token count of the count completion.
        flush_milliseconds: Flush in milliseconds.
        cancellation_check: Cancellation check.

    """

    session_id: str
    request_id: str
    prompt: str
    sampling_parameters: object
    engine: Engine
    timeout_seconds: float
    count_completion_tokens: CompletionCounter
    flush_milliseconds: float = 0.0
    cancellation_check: CancelCheck = None


async def _is_cancel_requested(cancellation_check: CancelCheck) -> bool:
    """Return whether the optional cancellation callback has fired.

    Args:
        cancellation_check: Cancellation check.

    Returns:
        Whether the optional cancellation callback has fired.

    """
    if cancellation_check is None:
        return False
    result = cancellation_check()
    if asyncio.iscoroutine(result):
        result = await result
    return bool(result)


async def stream_timed(
    request: StreamConfig,
) -> AsyncGenerator[EngineOutput, None]:
    """Stream generation with timeout and cancellation support.

    Args:
        request: Request to run.

    Yields:
        Generation with timeout and cancellation support.

    Raises:
        StreamCancelledError: The operation fails with this error.
        TimeoutError: The wait ran out of time.

    """
    stream = request.engine.generate_stream(
        prompt=request.prompt,
        sampling_parameters=request.sampling_parameters,
        request_id=request.request_id,
    )
    try:
        async with asyncio.timeout(request.timeout_seconds):
            async for out in stream:
                if await _is_cancel_requested(request.cancellation_check):
                    get_metrics().engine_abort_retryable_total.add(1, {"reason": "cancelled"})
                    await request.engine.abort(request.request_id)
                    raise StreamCancelledError
                yield out
    except TimeoutError:
        get_metrics().engine_abort_retryable_total.add(1, {"reason": "timeout"})
        await request.engine.abort(request.request_id)
        raise


__all__ = ["CancelCheck", "CompletionCounter", "StreamConfig", "stream_timed"]
