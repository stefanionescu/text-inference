"""vLLM engine adapter.

This module provides the VLLMEngine class backed by vLLM's AsyncLLM.

Key Features:
    1. Streaming generation with EngineOutput conversion
    2. Request abortion for cancellation support
    3. Non-preemptive prefix-cache reset for memory management
"""

from __future__ import annotations

import logging
from src.state.engines import EngineOutput
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.engines.sampling import SamplingParametersRequest
    from collections.abc import AsyncGenerator, AsyncIterator, Callable, Sequence

    type SamplingParametersFactory = Callable[..., object]

logger = logging.getLogger(__name__)


class _VLLMCompletion(Protocol):
    """vLLM completion fields consumed by the adapter."""

    @property
    def text(self) -> str:
        """Cumulative completion text."""
        raise NotImplementedError

    @property
    def token_ids(self) -> Sequence[int]:
        """Cumulative completion token identifiers."""
        raise NotImplementedError


class _VLLMOutput(Protocol):
    """vLLM streaming result fields consumed by the adapter."""

    @property
    def outputs(self) -> Sequence[_VLLMCompletion]:
        """Completion outputs in this result."""
        raise NotImplementedError

    @property
    def finished(self) -> bool:
        """Whether generation is complete."""
        raise NotImplementedError


class _VLLMRuntime(Protocol):
    """vLLM runtime behavior consumed by the adapter."""

    def generate(
        self,
        *,
        prompt: str,
        sampling_params: object,
        request_id: str,
    ) -> AsyncIterator[_VLLMOutput]:
        """Start one asynchronous generation stream."""
        raise NotImplementedError(prompt, sampling_params, request_id)

    async def abort(self, request_id: str) -> None:
        """Abort one generation request."""
        raise NotImplementedError(request_id)

    def shutdown(self) -> None:
        """Release runtime workers."""
        raise NotImplementedError

    async def reset_prefix_cache(
        self,
        *,
        reset_running_requests: bool = False,
        reset_connector: bool = False,
    ) -> bool:
        """Reset the prefix cache."""
        raise NotImplementedError(reset_running_requests, reset_connector)


class VLLMEngine:
    """vLLM-based inference engine with cache management.

    Attributes:
        _engine: The underlying vLLM AsyncLLM instance.

    """

    can_reset_cache = True

    def __init__(
        self,
        llm_engine: _VLLMRuntime,
        sampling_parameters_factory: SamplingParametersFactory,
    ) -> None:
        """Initialize the vLLM engine adapter."""
        self._engine = llm_engine
        self._sampling_parameters_factory = sampling_parameters_factory

    def create_sampling_parameters(self, request: SamplingParametersRequest) -> object:
        """Create vLLM 0.25 sampling parameters."""
        return self._sampling_parameters_factory(
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k,
            min_p=request.min_p,
            repetition_penalty=request.repetition_penalty,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            max_tokens=request.maximum_tokens,
            stop=request.stop,
            logit_bias=request.logit_bias,
        )

    async def generate_stream(
        self,
        prompt: str,
        sampling_parameters: object,
        request_id: str,
    ) -> AsyncGenerator[EngineOutput, None]:
        """Stream generation using vLLM's generate API.

        Args:
            prompt: The formatted prompt to generate from.
            sampling_parameters: vLLM SamplingParams instance.
            request_id: Unique identifier for tracking/abortion.

        Yields:
            EngineOutput with cumulative text and completion status.

        """
        engine = self._engine
        stream = engine.generate(
            prompt=prompt,
            sampling_params=sampling_parameters,
            request_id=request_id,
        )
        async for output in stream:
            completion = output.outputs[0]
            yield EngineOutput(
                text=completion.text,
                token_ids=list(completion.token_ids),
                is_finished=output.finished,
            )

    async def abort(self, request_id: str) -> None:
        """Abort a vLLM generation request."""
        await self._engine.abort(request_id)

    async def shutdown(self) -> None:
        """Shutdown the vLLM engine."""
        self._engine.shutdown()
        logger.info("vLLM: engine shutdown complete")

    async def reset_caches(self, reason: str) -> bool:
        """Attempt a prefix reset without preempting active requests."""
        logger.info("resetting vLLM cache (reason=%s)", reason)
        return await self._engine.reset_prefix_cache(
            reset_running_requests=False,
            reset_connector=False,
        )


__all__ = ["VLLMEngine"]
