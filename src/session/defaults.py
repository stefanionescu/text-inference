"""Default session-layer settings derived from static config values."""

from __future__ import annotations

from config.model.selection import MODEL
from config.runtime.cache import CACHE_RESET_INTERVAL_SECONDS
from src.state.settings import ModelSettings, SamplingSettings, SessionSettings
from config.limits import (
    MIN_P_MAX,
    MIN_P_MIN,
    TOP_K_MAX,
    TOP_K_MIN,
    TOP_P_MAX,
    TOP_P_MIN,
    TEMPERATURE_MAX,
    TEMPERATURE_MIN,
    PROMPT_MAX_TOKENS,
    PRESENCE_PENALTY_MAX,
    PRESENCE_PENALTY_MIN,
    FREQUENCY_PENALTY_MAX,
    FREQUENCY_PENALTY_MIN,
    MAXIMUM_OUTPUT_TOKENS,
    MAXIMUM_CONTEXT_LENGTH,
    REPETITION_PENALTY_MAX,
    REPETITION_PENALTY_MIN,
    STREAM_FLUSH_MILLISECONDS,
    USER_UTTERANCE_MAX_TOKENS,
)
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

DEFAULT_SESSION_SETTINGS = SessionSettings(
    maximum_context_length=MAXIMUM_CONTEXT_LENGTH,
    maximum_output_tokens=MAXIMUM_OUTPUT_TOKENS,
    maximum_prompt_tokens=PROMPT_MAX_TOKENS,
    maximum_user_utterance_tokens=USER_UTTERANCE_MAX_TOKENS,
    stream_flush_milliseconds=STREAM_FLUSH_MILLISECONDS,
    cache_reset_interval_seconds=CACHE_RESET_INTERVAL_SECONDS,
)
DEFAULT_MODEL_SETTINGS = ModelSettings(
    source=MODEL,
    runtime_quantization=None,
)
DEFAULT_SAMPLING_SETTINGS = SamplingSettings(
    temperature=TEMPERATURE,
    top_p=TOP_P,
    top_k=TOP_K,
    min_p=MIN_P,
    repetition_penalty=REPETITION_PENALTY,
    presence_penalty=PRESENCE_PENALTY,
    frequency_penalty=FREQUENCY_PENALTY,
    minimum_temperature=TEMPERATURE_MIN,
    maximum_temperature=TEMPERATURE_MAX,
    minimum_top_p=TOP_P_MIN,
    maximum_top_p=TOP_P_MAX,
    minimum_top_k=TOP_K_MIN,
    maximum_top_k=TOP_K_MAX,
    minimum_min_p=MIN_P_MIN,
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

__all__ = [
    "DEFAULT_MODEL_SETTINGS",
    "DEFAULT_SAMPLING_SETTINGS",
    "DEFAULT_SESSION_SETTINGS",
]
