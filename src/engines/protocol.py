"""Engine interface and backend-independent sampling and output records."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
from dataclasses import dataclass

if TYPE_CHECKING:
    from collections.abc import AsyncIterator


@dataclass(frozen=True)
class SamplingParametersRequest:
    """Parameters needed to create engine-specific sampling settings.

    Attributes:
        temperature: Temperature for this generation, after client overrides replace server defaults.
        top_p: Top-P cutoff for this generation.
        top_k: Top-K cutoff for this generation.
        min_p: Minimum token probability for this generation.
        repetition_penalty: Penalty on repeated tokens for this generation.
        presence_penalty: Penalty on tokens already present for this generation.
        frequency_penalty: Penalty that grows with token frequency for this generation.
        maximum_tokens: Output token limit, taken from the session settings.
        stop: Stop strings that end the generation, taken from the sampling settings.
        logit_bias: Bias per token ID, or None when no bias applies.

    """

    temperature: float = 1.0
    top_p: float = 1.0
    top_k: int = -1
    min_p: float = 0.0
    repetition_penalty: float = 1.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0
    maximum_tokens: int = 256
    stop: list[str] | None = None
    logit_bias: dict[int, float] | None = None


@dataclass(slots=True)
class EngineOutput:
    """Unified output format for streaming generation.

    Attributes:
        text: Cumulative completion text so far.
        token_ids: Cumulative completion token IDs, or None when the backend omits them.
        is_finished: Whether the backend marks this output as its last.

    """

    text: str
    token_ids: list[int] | None = None
    is_finished: bool = False


class CompletionText(Protocol):
    """Completion text that every backend adapter reads from its runtime."""

    @property
    def text(self) -> str:
        """Cumulative completion text.

        Raises:
            NotImplementedError: This stub always raises; a backend completion object supplies the text.

        """
        raise NotImplementedError


class Engine(Protocol):
    """Inference behavior required by the application runtime.

    Attributes:
        can_reset_cache: Whether `reset_caches` can succeed; the runtime builds a reset coordinator only when True.

    """

    can_reset_cache: bool

    def create_sampling_parameters(self, request: SamplingParametersRequest) -> object:
        """Create sampling parameters for this exact backend version.

        Args:
            request: Backend-independent sampling values for one generation.

        Returns:
            Sampling object in the form this backend expects.

        Raises:
            NotImplementedError: This stub always raises; each backend builds its own object.

        """
        raise NotImplementedError(request)

    def generate_stream(
        self,
        prompt: str,
        sampling_parameters: object,
        request_id: str,
    ) -> AsyncIterator[EngineOutput]:
        """Stream generation outputs.

        Args:
            prompt: Formatted prompt text to complete.
            sampling_parameters: Object from `create_sampling_parameters` on the same engine.
            request_id: ID that a later `abort` call uses to stop this generation.

        Returns:
            EngineOutput instances with cumulative text and optional token IDs.

        Raises:
            NotImplementedError: This stub always raises; each backend supplies its own stream.

        """
        raise NotImplementedError(prompt, sampling_parameters, request_id)

    async def abort(self, request_id: str) -> None:
        """Abort an in-flight generation request.

        Args:
            request_id: ID that was passed to `generate_stream`.

        Raises:
            NotImplementedError: This stub always raises; each backend stops its own generations.

        """
        raise NotImplementedError(request_id)

    async def shutdown(self) -> None:
        """Shutdown the engine and release resources.

        Raises:
            NotImplementedError: This stub always raises; each backend releases its own resources.

        """
        raise NotImplementedError

    async def reset_caches(self, reason: str) -> bool:
        """Reset engine caches when the backend supports it.

        Args:
            reason: Label for the reset trigger, which backends write to their logs.

        Returns:
            True when the backend reset its caches, False when it declined or has no reset.

        Raises:
            NotImplementedError: This stub always raises; each backend decides how to reset.

        """
        raise NotImplementedError(reason)


__all__ = ["CompletionText", "Engine", "EngineOutput", "SamplingParametersRequest"]
