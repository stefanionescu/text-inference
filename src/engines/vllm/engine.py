"""vLLM engine adapter.

This module provides the VLLMEngine class backed by vLLM's AsyncLLM.

Key Features:
    1. Streaming generation with EngineOutput conversion
    2. Request abortion for cancellation support
    3. Non-preemptive prefix-cache reset for memory management
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
import logging

from src.engines.protocol import EngineOutput, CompletionText

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence, AsyncIterator, AsyncGenerator

    from src.engines.protocol import SamplingParametersRequest

    type SamplingParametersFactory = Callable[..., object]

logger = logging.getLogger(__name__)


class _VLLMCompletion(CompletionText, Protocol):
    """vLLM completion fields consumed by the adapter."""

    @property
    def token_ids(self) -> Sequence[int]:
        """Cumulative completion token identifiers.

        Raises:
            NotImplementedError: This stub always raises; the vLLM completion object supplies the IDs.

        """
        raise NotImplementedError


class _VLLMOutput(Protocol):
    """vLLM streaming result fields consumed by the adapter."""

    @property
    def outputs(self) -> Sequence[_VLLMCompletion]:
        """Completions in this vLLM result; the adapter reads the first one.

        Raises:
            NotImplementedError: This stub always raises; the vLLM result object supplies the completions.

        """
        raise NotImplementedError

    @property
    def finished(self) -> bool:
        """Whether vLLM marks this result as the last one for the request.

        Raises:
            NotImplementedError: This stub always raises; the vLLM result object supplies the flag.

        """
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
        """Start one asynchronous generation stream.

        Args:
            prompt: Formatted prompt text that vLLM completes.
            sampling_params: Sampling object built by the adapter factory.
            request_id: ID that vLLM tracks, which `abort` uses later.

        Returns:
            Async iterator of vLLM results for this request.

        Raises:
            NotImplementedError: This stub always raises; `AsyncLLM` supplies the stream.

        """
        raise NotImplementedError(prompt, sampling_params, request_id)

    async def abort(self, request_id: str) -> None:
        """Abort one generation request.

        Args:
            request_id: ID given to `generate` for the request to stop.

        Raises:
            NotImplementedError: This stub always raises; `AsyncLLM` performs the abort.

        """
        raise NotImplementedError(request_id)

    def shutdown(self) -> None:
        """Stop the vLLM workers; `VLLMEngine.shutdown` calls this on the event loop.

        Raises:
            NotImplementedError: This stub always raises; `AsyncLLM` performs the shutdown.

        """
        raise NotImplementedError

    async def reset_prefix_cache(
        self,
        *,
        reset_running_requests: bool = False,
        reset_connector: bool = False,
    ) -> bool:
        """Reset the prefix cache.

        Args:
            reset_running_requests: Whether vLLM also resets running requests; `VLLMEngine` passes False.
            reset_connector: Whether vLLM also resets its connector; `VLLMEngine` passes False.

        Returns:
            True when vLLM reset the prefix cache, False when it did not.

        Raises:
            NotImplementedError: This stub always raises; `AsyncLLM` performs the reset.

        """
        raise NotImplementedError(reset_running_requests, reset_connector)


class VLLMEngine:
    """vLLM-based inference engine with cache management.

    Attributes:
        can_reset_cache: Always True, because vLLM has a prefix-cache reset.

    """

    can_reset_cache = True

    def __init__(
        self,
        llm_engine: _VLLMRuntime,
        sampling_parameters_factory: SamplingParametersFactory,
    ) -> None:
        """Initialize the vLLM engine adapter.

        Args:
            llm_engine: vLLM runtime that serves every call.
            sampling_parameters_factory: Factory that receives the keywords built by `create_sampling_parameters`.

        """
        self._engine = llm_engine
        self._sampling_parameters_factory = sampling_parameters_factory

    def create_sampling_parameters(self, request: SamplingParametersRequest) -> object:
        """Create vLLM 0.25 sampling parameters.

        Args:
            request: Sampling values, passed to the factory under vLLM keyword names.

        Returns:
            The object built by the vLLM sampling factory.

        """
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

        Returns:
            Async generator of EngineOutput items.

        Yields:
            One EngineOutput per vLLM result, with the cumulative text and token IDs of its first completion.

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
        """Abort a vLLM generation request.

        Args:
            request_id: ID of the vLLM request to abort.

        """
        await self._engine.abort(request_id)

    async def shutdown(self) -> None:
        """Shutdown the vLLM engine."""
        self._engine.shutdown()
        logger.info("vLLM: engine shutdown complete")

    async def reset_caches(self, reason: str) -> bool:
        """Attempt a prefix reset without preempting active requests.

        Args:
            reason: Label written to the reset log line.

        Returns:
            The vLLM answer: True after a reset, False when vLLM did not reset.

        """
        logger.info("resetting vLLM cache (reason=%s)", reason)
        return await self._engine.reset_prefix_cache(
            reset_running_requests=False,
            reset_connector=False,
        )


__all__ = ["VLLMEngine"]
