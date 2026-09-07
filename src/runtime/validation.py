"""Environment validation helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from config.runtime.gpu import KV_DTYPES
from config.model.trt import TRT_MODEL_DTYPES
from src.tokens.validation import validate_tokenizer_exists
from config.model.quantization import QUANTIZATIONS_BY_ENGINE

if TYPE_CHECKING:
    from src.state.settings import ApplicationSettings


def _validate_numeric_bounds(settings: ApplicationSettings) -> list[str]:
    """Check numeric config values are within valid ranges."""
    errors: list[str] = []
    sampling_settings = settings.sampling

    bounds: tuple[tuple[str, float | int, float | int, float | int], ...] = (
        (
            "TEMPERATURE",
            sampling_settings.temperature,
            sampling_settings.minimum_temperature,
            sampling_settings.maximum_temperature,
        ),
        ("TOP_P", sampling_settings.top_p, sampling_settings.minimum_top_p, sampling_settings.maximum_top_p),
        ("TOP_K", sampling_settings.top_k, sampling_settings.minimum_top_k, sampling_settings.maximum_top_k),
        ("MIN_P", sampling_settings.min_p, sampling_settings.minimum_min_p, sampling_settings.maximum_min_p),
        (
            "REPETITION_PENALTY",
            sampling_settings.repetition_penalty,
            sampling_settings.minimum_repetition_penalty,
            sampling_settings.maximum_repetition_penalty,
        ),
        (
            "PRESENCE_PENALTY",
            sampling_settings.presence_penalty,
            sampling_settings.minimum_presence_penalty,
            sampling_settings.maximum_presence_penalty,
        ),
        (
            "FREQUENCY_PENALTY",
            sampling_settings.frequency_penalty,
            sampling_settings.minimum_frequency_penalty,
            sampling_settings.maximum_frequency_penalty,
        ),
        ("WEBSOCKET_IDLE_TIMEOUT_SECONDS", settings.websocket.idle_timeout_seconds, 1.0, 86400.0),
        ("GENERATION_TIMEOUT_SECONDS", settings.timeouts.generation_timeout_seconds, 1.0, 600.0),
        ("GPU_MEMORY_FRACTION", settings.gpu.gpu_memory_fraction, 0.01, 1.0),
    )

    for name, value, minimum_value, maximum_value in bounds:
        if not (minimum_value <= value <= maximum_value):
            errors.append(f"{name} must be {minimum_value}-{maximum_value}, got {value}")

    positive_ints: tuple[tuple[str, int], ...] = (
        ("PROMPT_MAX_TOKENS", settings.session.maximum_prompt_tokens),
        ("HISTORY_MAX_TOKENS", settings.history.trigger_tokens),
        ("USER_UTTERANCE_MAX_TOKENS", settings.session.maximum_user_utterance_tokens),
        ("MAXIMUM_CONTEXT_LENGTH", settings.session.maximum_context_length),
        ("MAXIMUM_OUTPUT_TOKENS", settings.session.maximum_output_tokens),
    )

    for name, value in positive_ints:
        if value <= 0:
            errors.append(f"{name} must be positive, got {value}")

    return errors


def _validate_required_settings(settings: ApplicationSettings) -> list[str]:
    """Validate settings that must be present for startup."""
    errors: list[str] = []
    if not settings.authentication.api_key:
        errors.append("API_KEY environment variable is required")
    if settings.websocket.maximum_connections is None:
        errors.append("MAX_CONCURRENT_CONNECTIONS environment variable is required")
    elif settings.websocket.maximum_connections <= 0:
        errors.append("MAX_CONCURRENT_CONNECTIONS must be a positive integer (>= 1)")
    if settings.history.target_tokens >= settings.history.trigger_tokens:
        errors.append(
            f"TRIMMED_HISTORY_LENGTH ({settings.history.target_tokens}) must be less than "
            f"HISTORY_MAX_TOKENS ({settings.history.trigger_tokens})",
        )
    return errors


def _validate_model_settings(settings: ApplicationSettings) -> list[str]:
    """Validate model selection settings."""
    errors: list[str] = []
    if not settings.model.source:
        errors.append("MODEL is required")
    return errors


def _validate_engine_settings(settings: ApplicationSettings) -> list[str]:
    """Validate engine and quantization settings."""
    errors: list[str] = []
    if settings.engine.inference_engine not in QUANTIZATIONS_BY_ENGINE:
        errors.append(
            f"INFERENCE_ENGINE must be one of {tuple(QUANTIZATIONS_BY_ENGINE)}, "
            f"got: {settings.engine.inference_engine}",
        )
    if settings.gpu.key_value_cache_precision not in KV_DTYPES:
        errors.append(f"KV_DTYPE must be one of {sorted(KV_DTYPES)}, got: {settings.gpu.key_value_cache_precision}")
    if settings.engine.inference_engine == "trt":
        if settings.engine.trt_precision not in TRT_MODEL_DTYPES:
            errors.append(f"TRT_DTYPE must be one of {sorted(TRT_MODEL_DTYPES)}, got: {settings.engine.trt_precision}")
        if settings.engine.trt_maximum_batch_size <= 0:
            errors.append(f"TRT_MAX_BATCH_SIZE must be positive, got {settings.engine.trt_maximum_batch_size}")
    if settings.model.runtime_quantization is not None:
        valid_quantizations = QUANTIZATIONS_BY_ENGINE.get(settings.engine.inference_engine)
        if valid_quantizations is not None and settings.model.runtime_quantization not in valid_quantizations:
            errors.append(
                f"Invalid RUNTIME_QUANTIZATION='{settings.model.runtime_quantization}' for "
                f"{settings.engine.inference_engine}. "
                f"Valid formats: {', '.join(valid_quantizations)}",
            )
    return errors


def _validate_tokenizer_settings(settings: ApplicationSettings) -> list[str]:
    """Validate tokenizer availability for the configured model."""
    if not settings.model.source:
        return []
    result = validate_tokenizer_exists(settings.model.source)
    if result.is_valid:
        return []
    return [f"MODEL tokenizer validation failed:\n{result.error_message}"]


def validate_settings(settings: ApplicationSettings) -> None:
    """Validate resolved runtime settings once during startup."""
    errors: list[str] = []
    errors.extend(_validate_required_settings(settings))
    errors.extend(_validate_model_settings(settings))
    errors.extend(_validate_engine_settings(settings))
    errors.extend(_validate_tokenizer_settings(settings))
    errors.extend(_validate_numeric_bounds(settings))
    if errors:
        raise ValueError("; ".join(errors))


__all__ = ["validate_settings"]
