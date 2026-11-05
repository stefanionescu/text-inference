"""Resolved runtime settings state.

These dataclasses represent the process-level runtime configuration for the
inference server. They are plain state objects and intentionally contain no
loading logic.
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping

type EnvironmentValues = Mapping[str, str]


@dataclass(frozen=True, slots=True)
class AuthenticationSettings:
    """Hold the server API key that every WebSocket handshake must present.

    `validate_settings` rejects startup when the key is missing, and
    `authenticate_websocket` compares each client's key against it.

    Attributes:
        api_key: Key of the API.

    """

    api_key: str | None


@dataclass(frozen=True, slots=True)
class ModelSettings:
    """Model selection settings.

    Attributes:
        source: Source checkpoint to read.
        runtime_quantization: Runtime quantization.

    """

    source: str | None
    runtime_quantization: str | None


@dataclass(frozen=True, slots=True)
class EngineSettings:
    """Inference engine settings.

    Attributes:
        inference_engine: Inference engine.
        trt_precision: TensorRT precision.
        trt_maximum_batch_size: TensorRT maximum batch size.
        is_eager_execution_enforced: Whether eager execution is enforced.
        is_logging_enabled: Whether logging is enabled.

    """

    inference_engine: str
    trt_precision: str
    trt_maximum_batch_size: int
    is_eager_execution_enforced: bool
    is_logging_enabled: bool


@dataclass(frozen=True, slots=True)
class GPUSettings:
    """GPU runtime settings.

    Attributes:
        gpu_memory_fraction: GPU memory fraction.
        key_value_cache_precision: Key value cache precision.
        gpu_compute_capability: GPU compute capability.

    """

    gpu_memory_fraction: float
    key_value_cache_precision: str
    gpu_compute_capability: str


@dataclass(frozen=True, slots=True)
class HistorySettings:
    """Conversation history budget settings.

    Attributes:
        trigger_tokens: Token count of the trigger.
        target_tokens: Token count of the target.

    """

    trigger_tokens: int
    target_tokens: int


@dataclass(frozen=True, slots=True)
class SessionSettings:
    """Session size and streaming settings.

    Attributes:
        maximum_context_length: Largest allowed context length.
        maximum_output_tokens: Largest allowed output tokens.
        maximum_prompt_tokens: Largest allowed prompt tokens.
        maximum_user_utterance_tokens: Largest allowed user utterance tokens.
        stream_flush_milliseconds: Stream flush in milliseconds.
        cache_reset_interval_seconds: Cache reset interval in seconds.

    """

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
    """Sampling parameter defaults and bounds.

    Attributes:
        temperature: Sampling temperature.
        top_p: Top-P sampling value.
        top_k: Top-K sampling value.
        min_p: Minimum-probability sampling value.
        repetition_penalty: Repetition penalty.
        presence_penalty: Presence penalty.
        frequency_penalty: Frequency penalty.
        minimum_temperature: Smallest allowed temperature.
        maximum_temperature: Largest allowed temperature.
        minimum_top_p: Smallest allowed top p.
        maximum_top_p: Largest allowed top p.
        minimum_top_k: Smallest allowed top k.
        maximum_top_k: Largest allowed top k.
        minimum_min_p: Smallest allowed min p.
        maximum_min_p: Largest allowed min p.
        minimum_repetition_penalty: Smallest allowed repetition penalty.
        maximum_repetition_penalty: Largest allowed repetition penalty.
        minimum_presence_penalty: Smallest allowed presence penalty.
        maximum_presence_penalty: Largest allowed presence penalty.
        minimum_frequency_penalty: Smallest allowed frequency penalty.
        maximum_frequency_penalty: Largest allowed frequency penalty.
        inference_stop: Inference stop.
        logit_bias: Logit bias.

    """

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
    """Request timeout settings.

    Attributes:
        generation_timeout_seconds: Generation timeout in seconds.

    """

    generation_timeout_seconds: float


@dataclass(frozen=True, slots=True)
class WebSocketSettings:
    """WebSocket protocol and rate-limit settings.

    Attributes:
        maximum_connections: Largest allowed connections.
        idle_timeout_seconds: Idle timeout in seconds.
        watchdog_tick_seconds: Watchdog tick in seconds.
        handshake_acquire_timeout_seconds: Handshake acquire timeout in seconds.
        protocol_version: Version of the protocol.
        maximum_message_bytes: Largest allowed message bytes.
        rate_limit_window_seconds: Rate limit window in seconds.
        maximum_messages_per_window: Largest allowed messages per window.
        maximum_cancels_per_window: Largest allowed cancels per window.
        authentication_failures_per_window: Authentication failures per window.

    """

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
    """Complete application settings.

    Attributes:
        authentication: Authentication settings.
        model: Model name or local checkpoint path.
        engine: Inference engine that serves the request.
        gpu: GPU settings.
        history: Conversation history to use.
        session: Session to use.
        sampling: Sampling overrides of the request.
        timeouts: Timeout settings.
        websocket: WebSocket connection of the client.

    """

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
