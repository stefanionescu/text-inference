"""TensorRT-LLM public PyTorch backend adapter."""

from __future__ import annotations

import asyncio
import logging
from src.state.engines import EngineOutput
from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from src.engines.sampling import SamplingParametersRequest
    from collections.abc import AsyncGenerator, AsyncIterator, Callable, Sequence

    type SamplingParametersFactory = Callable[..., object]

logger = logging.getLogger(__name__)


class _TRTCompletion(Protocol):
    """TensorRT completion fields consumed by the adapter."""

    @property
    def text(self) -> str:
        """Cumulative completion text."""
        raise NotImplementedError

    @property
    def token_ids(self) -> Sequence[int] | None:
        """Cumulative completion token identifiers."""
        raise NotImplementedError


class _TRTChunk(Protocol):
    """TensorRT streaming result fields consumed by the adapter."""

    @property
    def outputs(self) -> Sequence[_TRTCompletion]:
        """Completion outputs in this chunk."""
        raise NotImplementedError

    @property
    def finished(self) -> bool:
        """Whether generation is complete."""
        raise NotImplementedError


class _TRTGeneration(Protocol):
    """TensorRT asynchronous generation behavior consumed by the adapter."""

    def __aiter__(self) -> AsyncIterator[_TRTChunk]:
        """Iterate over cumulative generation chunks."""
        raise NotImplementedError

    def abort(self) -> None:
        """Abort the active generation."""
        raise NotImplementedError


class _TRTRuntime(Protocol):
    """TensorRT runtime behavior consumed by the adapter."""

    def generate_async(
        self,
        prompt: str,
        sampling_params: object,
        *,
        streaming: bool,
    ) -> _TRTGeneration:
        """Start one asynchronous generation."""
        raise NotImplementedError(prompt, sampling_params, streaming)

    def shutdown(self) -> None:
        """Release runtime workers."""
        raise NotImplementedError


class TRTEngine:
    """TensorRT-LLM engine using its public PyTorch backend API."""

    def __init__(
        self,
        llm: _TRTRuntime,
        sampling_parameters_factory: SamplingParametersFactory,
        vocab_size: int,
    ) -> None:
        """Initialize the TensorRT-LLM adapter."""
        self._llm = llm
        self._sampling_parameters_factory = sampling_parameters_factory
        self._vocab_size = vocab_size
        self._inflight: dict[str, _TRTGeneration] = {}

    def create_sampling_parameters(self, request: SamplingParametersRequest) -> object:
        """Create TensorRT-LLM 1.3 sampling parameters."""
        embedding_bias = None
        if request.logit_bias:
            embedding_bias = [0.0] * self._vocab_size
            for token_id, bias in request.logit_bias.items():
                embedding_bias[token_id] = bias
        return self._sampling_parameters_factory(
            temperature=request.temperature,
            top_p=request.top_p,
            top_k=request.top_k if request.top_k > 0 else None,
            min_p=request.min_p,
            repetition_penalty=request.repetition_penalty,
            presence_penalty=request.presence_penalty,
            frequency_penalty=request.frequency_penalty,
            max_tokens=request.maximum_tokens,
            stop=request.stop,
            embedding_bias=embedding_bias,
        )

    async def generate_stream(
        self,
        prompt: str,
        sampling_parameters: object,
        request_id: str,
    ) -> AsyncGenerator[EngineOutput, None]:
        """Stream generation through the public asynchronous result API."""
        generation = self._llm.generate_async(prompt, sampling_parameters, streaming=True)
        self._inflight[request_id] = generation

        try:
            async for chunk in generation:
                completion = chunk.outputs[0]
                yield EngineOutput(
                    text=completion.text,
                    token_ids=list(completion.token_ids) if completion.token_ids is not None else None,
                    is_finished=chunk.finished,
                )
        finally:
            self._inflight.pop(request_id, None)

    async def abort(self, request_id: str) -> None:
        """Abort an in-flight request through its public result object."""
        pending = self._inflight.pop(request_id, None)
        if pending is None:
            return

        pending.abort()
        logger.info("TRT-LLM: cancelled request_id=%s", request_id)

    async def shutdown(self) -> None:
        """Shutdown TensorRT-LLM and release its worker resources."""
        pending_requests = tuple(self._inflight.values())
        self._inflight.clear()
        for pending in pending_requests:
            pending.abort()
        await asyncio.to_thread(self._llm.shutdown)
        logger.info("TRT-LLM: engine shutdown complete")

    async def reset_caches(self, reason: str) -> bool:
        """Report that TensorRT-LLM manages its own cache lifecycle."""
        logger.debug("TRT-LLM: cache reset requested but unsupported (reason=%s)", reason)
        return False


__all__ = ["TRTEngine"]
