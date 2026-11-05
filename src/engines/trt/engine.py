"""TensorRT-LLM public PyTorch backend adapter."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
import asyncio
import logging

from src.engines.protocol import EngineOutput, CompletionText

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence, AsyncIterator, AsyncGenerator

    from src.engines.protocol import SamplingParametersRequest

    type SamplingParametersFactory = Callable[..., object]

logger = logging.getLogger(__name__)


class _TRTCompletion(CompletionText, Protocol):
    """TensorRT completion fields consumed by the adapter."""

    @property
    def token_ids(self) -> Sequence[int] | None:
        """Cumulative completion token IDs, or None when TensorRT omits them.

        Raises:
            NotImplementedError: This stub always raises; the TensorRT completion object supplies the IDs.

        """
        raise NotImplementedError


class _TRTChunk(Protocol):
    """TensorRT streaming result fields consumed by the adapter."""

    @property
    def outputs(self) -> Sequence[_TRTCompletion]:
        """Completions in this TensorRT chunk; the adapter reads the first one.

        Raises:
            NotImplementedError: This stub always raises; the TensorRT chunk supplies the completions.

        """
        raise NotImplementedError

    @property
    def finished(self) -> bool:
        """Whether TensorRT marks this chunk as the last, so `generate_stream` skips its abort.

        Raises:
            NotImplementedError: This stub always raises; the TensorRT chunk supplies the flag.

        """
        raise NotImplementedError


class _TRTGeneration(Protocol):
    """TensorRT asynchronous generation behavior consumed by the adapter."""

    def __aiter__(self) -> AsyncIterator[_TRTChunk]:
        """Iterate over cumulative generation chunks.

        Returns:
            Async iterator over chunks with cumulative text.

        Raises:
            NotImplementedError: This stub always raises; the TensorRT generation supplies the iterator.

        """
        raise NotImplementedError

    def abort(self) -> None:
        """Abort the active generation.

        Raises:
            NotImplementedError: This stub always raises; the TensorRT generation performs the abort.

        """
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
        """Start one asynchronous generation.

        Args:
            prompt: Formatted prompt text that TensorRT completes.
            sampling_params: TensorRT sampling object built by the adapter factory.
            streaming: Whether TensorRT streams chunks; `generate_stream` always passes True.

        Returns:
            Generation handle that the adapter iterates and can abort.

        Raises:
            NotImplementedError: This stub always raises; the TensorRT LLM object starts the generation.

        """
        raise NotImplementedError(prompt, sampling_params, streaming)

    def shutdown(self) -> None:
        """Stop the TensorRT workers; `TRTEngine.shutdown` runs this in a worker thread.

        Raises:
            NotImplementedError: This stub always raises; the TensorRT LLM object performs the shutdown.

        """
        raise NotImplementedError


class TRTEngine:
    """TensorRT-LLM engine using its public PyTorch backend API.

    Attributes:
        can_reset_cache: Always False, because TensorRT-LLM manages its own cache.

    """

    can_reset_cache = False

    def __init__(
        self,
        llm: _TRTRuntime,
        sampling_parameters_factory: SamplingParametersFactory,
        vocab_size: int,
    ) -> None:
        """Initialize the TensorRT-LLM adapter.

        Args:
            llm: TensorRT-LLM runtime that serves every call.
            sampling_parameters_factory: Factory for the TensorRT sampling object.
            vocab_size: Length of the `embedding_bias` list built from a logit bias.

        """
        self._llm = llm
        self._sampling_parameters_factory = sampling_parameters_factory
        self._vocab_size = vocab_size
        self._inflight: dict[str, _TRTGeneration] = {}

    def create_sampling_parameters(self, request: SamplingParametersRequest) -> object:
        """Create TensorRT-LLM 1.3 sampling parameters.

        Args:
            request: Sampling values; a non-positive `top_k` becomes None and `logit_bias` becomes `embedding_bias`.

        Returns:
            The object built by the TensorRT sampling factory.

        """
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
        self, prompt: str, sampling_parameters: object, request_id: str
    ) -> AsyncGenerator[EngineOutput, None]:
        """Stream results and abort unfinished work when its consumer exits.

        Args:
            prompt: Formatted prompt to complete.
            sampling_parameters: Object from `create_sampling_parameters`.
            request_id: Key under which `abort` finds this generation.

        Returns:
            Async generator of EngineOutput items.

        Yields:
            One EngineOutput per TensorRT chunk, with cumulative text and any token IDs.

        """
        generation = self._llm.generate_async(prompt, sampling_parameters, streaming=True)
        self._inflight[request_id] = generation
        is_finished = False

        try:
            async for chunk in generation:
                completion = chunk.outputs[0]
                is_finished = chunk.finished
                yield EngineOutput(
                    text=completion.text,
                    token_ids=list(completion.token_ids) if completion.token_ids is not None else None,
                    is_finished=chunk.finished,
                )
        finally:
            pending = self._inflight.pop(request_id, None)
            if pending is not None and not is_finished:
                pending.abort()

    async def abort(self, request_id: str) -> None:
        """Abort an in-flight request through its public result object.

        Args:
            request_id: Key of the in-flight generation; an unknown key does nothing.

        """
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
        """Report that TensorRT-LLM manages its own cache lifecycle.

        Args:
            reason: Label written to the debug log line.

        Returns:
            Always False, because this adapter has no reset to run.

        """
        logger.debug("TRT-LLM: cache reset requested but unsupported (reason=%s)", reason)
        return False


__all__ = ["TRTEngine"]
