"""Backend-independent sampling parameter values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SamplingParametersRequest:
    """Parameters needed to create engine-specific sampling settings."""

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


__all__ = ["SamplingParametersRequest"]
