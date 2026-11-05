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
        temperature: Sampling temperature.
        top_p: Top-P sampling value.
        top_k: Top-K sampling value.
        min_p: Minimum-probability sampling value.
        repetition_penalty: Repetition penalty.
        presence_penalty: Presence penalty.
        frequency_penalty: Frequency penalty.
        maximum_tokens: Largest allowed tokens.
        stop: Stop strings of the generation.
        logit_bias: Logit bias.

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
        text: Text to process.
        token_ids: Token identifiers.
        is_finished: Whether it is finished.

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
            NotImplementedError: The backend does not implement this call.

        """
        raise NotImplementedError


class Engine(Protocol):
    """Inference behavior required by the application runtime.

    Attributes:
        can_reset_cache: Whether it can reset cache.

    """

    can_reset_cache: bool

    def create_sampling_parameters(self, request: SamplingParametersRequest) -> object:
        """Create sampling parameters for this exact backend version.

        Args:
            request: Request to run.

        Returns:
            Sampling parameters for this exact backend version.

        Raises:
            NotImplementedError: The backend does not implement this call.

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
            prompt: The input prompt text.
            sampling_parameters: Engine-specific sampling parameters.
            request_id: Unique identifier for this request.

        Returns:
            EngineOutput instances with cumulative text and optional token IDs.

        Raises:
            NotImplementedError: The backend does not implement this call.

        """
        raise NotImplementedError(prompt, sampling_parameters, request_id)

    async def abort(self, request_id: str) -> None:
        """Abort an in-flight generation request.

        Args:
            request_id: The request ID to abort.

        Raises:
            NotImplementedError: The backend does not implement this call.

        """
        raise NotImplementedError(request_id)

    async def shutdown(self) -> None:
        """Shutdown the engine and release resources.

        Raises:
            NotImplementedError: The backend does not implement this call.

        """
        raise NotImplementedError

    async def reset_caches(self, reason: str) -> bool:
        """Reset engine caches when the backend supports it.

        Args:
            reason: Reason text to report.

        Returns:
            Whether the check passes.

        Raises:
            NotImplementedError: The backend does not implement this call.

        """
        raise NotImplementedError(reason)


__all__ = ["CompletionText", "Engine", "EngineOutput", "SamplingParametersRequest"]
