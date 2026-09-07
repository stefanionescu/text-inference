"""Resolved runtime settings state.

These dataclasses represent the process-level runtime configuration for the
inference server. They are plain state objects and intentionally contain no
loading logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

EnvironmentValues = Mapping[str, str]


@dataclass(frozen=True, slots=True)
class AuthenticationSettings:
    """Authentication settings."""

    api_key: str | None


@dataclass(frozen=True, slots=True)
class ModelSettings:
    """Model selection settings."""

    source: str | None
    runtime_quantization: str | None


@dataclass(frozen=True, slots=True)
class EngineSettings:
    """Inference engine settings."""

    inference_engine: str
    trt_precision: str
    trt_maximum_batch_size: int
    is_eager_execution_enforced: bool
    is_logging_enabled: bool


@dataclass(frozen=True, slots=True)
class GPUSettings:
    """GPU runtime settings."""

    gpu_memory_fraction: float
    key_value_cache_precision: str
    gpu_compute_capability: str


@dataclass(frozen=True, slots=True)
class HistorySettings:
    """Conversation history budget settings."""

    trigger_tokens: int
    target_tokens: int


@dataclass(frozen=True, slots=True)
class SessionSettings:
    """Session size and streaming settings."""

    maximum_context_length: int
    maximum_output_tokens: int
    maximum_prompt_tokens: int
    maximum_user_utterance_tokens: int
    stream_flush_milliseconds: float
    cache_reset_interval_seconds: float

    @property
    def maximum_sequence_length(self) -> int:
        """The total prompt and generation capacity."""
        return self.maximum_context_length + self.maximum_output_tokens


@dataclass(frozen=True, slots=True)
class SamplingSettings:
    """Sampling parameter defaults and bounds."""

    temperature: float
    top_p: float
    top_k: int
    min_p: float
    repetition_penalty: float
    presence_penalty: float
    frequency_penalty: float
    minimum_temperature: float
    maximum_temperature: float
    minimum_top_p: float
    maximum_top_p: float
    minimum_top_k: int
    maximum_top_k: int
    minimum_min_p: float
    maximum_min_p: float
    minimum_repetition_penalty: float
    maximum_repetition_penalty: float
    minimum_presence_penalty: float
    maximum_presence_penalty: float
    minimum_frequency_penalty: float
    maximum_frequency_penalty: float
    inference_stop: tuple[str, ...]
    logit_bias: Mapping[str, float]


@dataclass(frozen=True, slots=True)
class TimeoutSettings:
    """Request timeout settings."""

    generation_timeout_seconds: float


@dataclass(frozen=True, slots=True)
class WebSocketSettings:
    """WebSocket protocol and rate-limit settings."""

    maximum_connections: int | None
    idle_timeout_seconds: float
    watchdog_tick_seconds: float
    handshake_acquire_timeout_seconds: float
    protocol_version: int
    maximum_message_bytes: int
    rate_limit_window_seconds: float
    maximum_messages_per_window: int
    maximum_cancels_per_window: int
    authentication_failures_per_window: int


@dataclass(frozen=True, slots=True)
class ApplicationSettings:
    """Complete application settings."""

    authentication: AuthenticationSettings
    model: ModelSettings
    engine: EngineSettings
    gpu: GPUSettings
    history: HistorySettings
    session: SessionSettings
    sampling: SamplingSettings
    timeouts: TimeoutSettings
    websocket: WebSocketSettings


__all__ = [
    "ApplicationSettings",
    "AuthenticationSettings",
    "EngineSettings",
    "EnvironmentValues",
    "GPUSettings",
    "HistorySettings",
    "ModelSettings",
    "SamplingSettings",
    "SessionSettings",
    "TimeoutSettings",
    "WebSocketSettings",
]
