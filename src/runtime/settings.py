"""Runtime settings assembly."""

from __future__ import annotations

import os

from config.limits import (
    MIN_P_MAX,
    TOP_K_MAX,
    TOP_K_MIN,
    TOP_P_MAX,
    TOP_P_MIN,
    MIN_P_LOWER,
    TEMPERATURE_MAX,
    TEMPERATURE_MIN,
    PRESENCE_PENALTY_MAX,
    PRESENCE_PENALTY_MIN,
    FREQUENCY_PENALTY_MAX,
    FREQUENCY_PENALTY_MIN,
    REPETITION_PENALTY_MAX,
    REPETITION_PENALTY_MIN,
)
from config.security import API_KEY
from config.model.trt import TRT_DTYPE, TRT_MAX_BATCH_SIZE
from config.runtime.gpu import KV_DTYPE, GPU_SM_ARCH, GPU_MEMORY_FRACTION
from src.runtime.config import (
    GPUSettings,
    ModelSettings,
    EngineSettings,
    HistorySettings,
    SessionSettings,
    TimeoutSettings,
    SamplingSettings,
    EnvironmentValues,
    WebSocketSettings,
    ApplicationSettings,
    AuthenticationSettings,
)
from src.runtime.limits import LimitSettings, read_limit_settings
from config.runtime.cache import CACHE_RESET_INTERVAL_SECONDS
from config.prompt.sampling import (
    MIN_P,
    TOP_K,
    TOP_P,
    LOGIT_BIAS,
    TEMPERATURE,
    INFERENCE_STOP,
    PRESENCE_PENALTY,
    FREQUENCY_PENALTY,
    REPETITION_PENALTY,
)
from config.runtime.timeouts import GENERATION_TIMEOUT_SECONDS
from config.runtime.websocket import (
    WEBSOCKET_PROTOCOL_VERSION,
    WEBSOCKET_MAX_MESSAGE_BYTES,
    AUTHENTICATION_FAILURE_LIMIT,
    WEBSOCKET_CANCELS_PER_WINDOW,
    WEBSOCKET_MESSAGES_PER_WINDOW,
    WEBSOCKET_RATE_WINDOW_SECONDS,
    WEBSOCKET_IDLE_TIMEOUT_SECONDS,
    WEBSOCKET_WATCHDOG_TICK_SECONDS,
    HANDSHAKE_ACQUIRE_TIMEOUT_SECONDS,
)


def _read_nullable_environment_text(
    environment: EnvironmentValues,
    name: str,
    default: str | None,
) -> str | None:
    """Read a nullable stripped string setting from an environment mapping."""
    raw_value = environment.get(name)
    if raw_value is None:
        return default
    normalized = str(raw_value).strip()
    return normalized or None


def _read_environment_integer(environment: EnvironmentValues, name: str, default: int) -> int:
    """Read an integer setting from an environment mapping."""
    raw_value = environment.get(name)
    if raw_value is None or str(raw_value).strip() == "":
        return default
    try:
        return int(str(raw_value).strip())
    except (TypeError, ValueError) as exception:
        message = f"{name} must be an integer, got {raw_value!r}"
        raise ValueError(message) from exception


def _read_environment_float(environment: EnvironmentValues, name: str, default: float) -> float:
    """Read a float setting from an environment mapping."""
    raw_value = environment.get(name)
    if raw_value is None or str(raw_value).strip() == "":
        return default
    try:
        return float(str(raw_value).strip())
    except (TypeError, ValueError) as exception:
        message = f"{name} must be a float, got {raw_value!r}"
        raise ValueError(message) from exception


def _read_environment_boolean(environment: EnvironmentValues, name: str) -> bool:
    """Read an exact zero-or-one boolean setting."""
    raw_value = environment.get(name)
    if raw_value is None:
        return False
    if raw_value == "0":
        return False
    if raw_value == "1":
        return True
    message = f"{name} must be 0 or 1, got {raw_value!r}"
    raise ValueError(message)


def _build_history_settings(limits: LimitSettings) -> HistorySettings:
    """Build history trimming settings from environment values."""
    trigger_tokens = int(limits["HISTORY_MAX_TOKENS"])
    target_tokens = int(limits["TRIMMED_HISTORY_LENGTH"])
    return HistorySettings(
        trigger_tokens=trigger_tokens,
        target_tokens=target_tokens,
    )


def _build_session_settings(environment: EnvironmentValues, limits: LimitSettings) -> SessionSettings:
    """Build session limits and cache settings from environment values."""
    maximum_context_length = int(limits["MAXIMUM_CONTEXT_LENGTH"])
    maximum_output_tokens = int(limits["MAXIMUM_OUTPUT_TOKENS"])
    maximum_prompt_tokens = int(limits["PROMPT_MAX_TOKENS"])
    maximum_user_utterance_tokens = int(limits["USER_UTTERANCE_MAX_TOKENS"])
    stream_flush_milliseconds = float(limits["STREAM_FLUSH_MILLISECONDS"])
    return SessionSettings(
        maximum_context_length=maximum_context_length,
        maximum_output_tokens=maximum_output_tokens,
        maximum_prompt_tokens=maximum_prompt_tokens,
        maximum_user_utterance_tokens=maximum_user_utterance_tokens,
        stream_flush_milliseconds=stream_flush_milliseconds,
        cache_reset_interval_seconds=_read_environment_float(
            environment,
            "CACHE_RESET_INTERVAL_SECONDS",
            CACHE_RESET_INTERVAL_SECONDS,
        ),
    )


def _build_sampling_settings(environment: EnvironmentValues) -> SamplingSettings:
    """Build sampling settings from environment values."""
    return SamplingSettings(
        temperature=_read_environment_float(environment, "TEMPERATURE", TEMPERATURE),
        top_p=_read_environment_float(environment, "TOP_P", TOP_P),
        top_k=_read_environment_integer(environment, "TOP_K", TOP_K),
        min_p=_read_environment_float(environment, "MIN_P", MIN_P),
        repetition_penalty=_read_environment_float(environment, "REPETITION_PENALTY", REPETITION_PENALTY),
        presence_penalty=_read_environment_float(environment, "PRESENCE_PENALTY", PRESENCE_PENALTY),
        frequency_penalty=_read_environment_float(environment, "FREQUENCY_PENALTY", FREQUENCY_PENALTY),
        minimum_temperature=TEMPERATURE_MIN,
        maximum_temperature=TEMPERATURE_MAX,
        minimum_top_p=TOP_P_MIN,
        maximum_top_p=TOP_P_MAX,
        minimum_top_k=TOP_K_MIN,
        maximum_top_k=TOP_K_MAX,
        minimum_min_p=MIN_P_LOWER,
        maximum_min_p=MIN_P_MAX,
        minimum_repetition_penalty=REPETITION_PENALTY_MIN,
        maximum_repetition_penalty=REPETITION_PENALTY_MAX,
        minimum_presence_penalty=PRESENCE_PENALTY_MIN,
        maximum_presence_penalty=PRESENCE_PENALTY_MAX,
        minimum_frequency_penalty=FREQUENCY_PENALTY_MIN,
        maximum_frequency_penalty=FREQUENCY_PENALTY_MAX,
        inference_stop=tuple(INFERENCE_STOP),
        logit_bias=dict(LOGIT_BIAS),
    )


def _build_websocket_settings(environment: EnvironmentValues, limits: LimitSettings) -> WebSocketSettings:
    """Build WebSocket settings from environment values."""
    return WebSocketSettings(
        maximum_connections=limits["MAX_CONCURRENT_CONNECTIONS"],
        idle_timeout_seconds=_read_environment_float(
            environment,
            "WEBSOCKET_IDLE_TIMEOUT_SECONDS",
            WEBSOCKET_IDLE_TIMEOUT_SECONDS,
        ),
        watchdog_tick_seconds=_read_environment_float(
            environment,
            "WEBSOCKET_WATCHDOG_TICK_SECONDS",
            WEBSOCKET_WATCHDOG_TICK_SECONDS,
        ),
        handshake_acquire_timeout_seconds=_read_environment_float(
            environment,
            "WEBSOCKET_HANDSHAKE_ACQUIRE_TIMEOUT_SECONDS",
            HANDSHAKE_ACQUIRE_TIMEOUT_SECONDS,
        ),
        protocol_version=_read_environment_integer(
            environment, "WEBSOCKET_PROTOCOL_VERSION", WEBSOCKET_PROTOCOL_VERSION
        ),
        maximum_message_bytes=_read_environment_integer(
            environment, "WEBSOCKET_MAX_MESSAGE_BYTES", WEBSOCKET_MAX_MESSAGE_BYTES
        ),
        rate_limit_window_seconds=_read_environment_float(
            environment,
            "WEBSOCKET_RATE_LIMIT_WINDOW_SECONDS",
            WEBSOCKET_RATE_WINDOW_SECONDS,
        ),
        maximum_messages_per_window=_read_environment_integer(
            environment,
            "WEBSOCKET_MESSAGES_PER_WINDOW",
            WEBSOCKET_MESSAGES_PER_WINDOW,
        ),
        maximum_cancels_per_window=_read_environment_integer(
            environment,
            "WEBSOCKET_CANCELS_PER_WINDOW",
            WEBSOCKET_CANCELS_PER_WINDOW,
        ),
        authentication_failures_per_window=_read_environment_integer(
            environment,
            "AUTHENTICATION_FAILURE_LIMIT",
            AUTHENTICATION_FAILURE_LIMIT,
        ),
    )


def read_settings(environment: EnvironmentValues | None = None) -> ApplicationSettings:
    """Resolve environment variables into one typed settings object."""
    active_environment = os.environ if environment is None else environment
    limits = read_limit_settings(environment=active_environment)
    inference_engine = active_environment.get("INFERENCE_ENGINE", "trt")
    if inference_engine not in {"trt", "vllm"}:
        message = f"INFERENCE_ENGINE must be 'trt' or 'vllm', got {inference_engine!r}"
        raise ValueError(message)
    engine_settings = EngineSettings(
        inference_engine=inference_engine,
        trt_precision=active_environment.get("TRT_DTYPE", TRT_DTYPE),
        trt_maximum_batch_size=_read_environment_integer(
            active_environment,
            "TRT_MAX_BATCH_SIZE",
            TRT_MAX_BATCH_SIZE,
        ),
        is_eager_execution_enforced=_read_environment_boolean(active_environment, "ENFORCE_EAGER"),
        is_logging_enabled=_read_environment_boolean(active_environment, "LOGS_ENABLED"),
    )
    gpu_settings = GPUSettings(
        gpu_memory_fraction=_read_environment_float(
            active_environment,
            "GPU_MEMORY_FRACTION",
            GPU_MEMORY_FRACTION,
        ),
        key_value_cache_precision=active_environment.get("KV_DTYPE", KV_DTYPE),
        gpu_compute_capability=active_environment.get("GPU_SM_ARCH", GPU_SM_ARCH),
    )
    timeout_settings = TimeoutSettings(
        generation_timeout_seconds=_read_environment_float(
            active_environment,
            "GENERATION_TIMEOUT_SECONDS",
            GENERATION_TIMEOUT_SECONDS,
        ),
    )
    return ApplicationSettings(
        authentication=AuthenticationSettings(
            api_key=_read_nullable_environment_text(active_environment, "API_KEY", API_KEY),
        ),
        model=ModelSettings(
            source=_read_nullable_environment_text(active_environment, "MODEL", None),
            runtime_quantization=_read_nullable_environment_text(active_environment, "RUNTIME_QUANTIZATION", None),
        ),
        engine=engine_settings,
        gpu=gpu_settings,
        history=_build_history_settings(limits),
        session=_build_session_settings(active_environment, limits),
        sampling=_build_sampling_settings(active_environment),
        timeouts=timeout_settings,
        websocket=_build_websocket_settings(active_environment, limits),
    )


__all__ = ["read_settings"]
