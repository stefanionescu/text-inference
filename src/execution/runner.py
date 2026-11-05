"""High-level generation runner.

This module provides the main interface for streaming generation,
handling:

1. Sampling Parameter Resolution
2. Prompt validation / metrics
3. Stream Processing with optional sanitization
4. Cancellation checks
"""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from dataclasses import dataclass

from opentelemetry import trace

from src.text.stream import StreamingSanitizer
from src.engines.protocol import SamplingParametersRequest
from src.session.requests import is_request_cancelled
from src.telemetry.instruments import get_metrics

from .controller import StreamConfig, StreamController

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

    from src.session.state import SessionState
    from src.runtime.config import SessionSettings, TimeoutSettings, SamplingSettings
    from src.engines.protocol import Engine
    from src.tokens.tokenizer import ThreadSafeTokenizer


@dataclass(frozen=True)
class GenerationRequest:
    """Inputs needed to stream one generation."""

    state: SessionState
    prompt: str
    engine: Engine
    tokenizer: ThreadSafeTokenizer
    session_settings: SessionSettings
    timeout_settings: TimeoutSettings
    sampling_settings: SamplingSettings
    request_id: str | None = None
    sampling_overrides: dict[str, float | int | bool] | None = None
    prompt_token_count: int | None = None


def _build_logit_bias_map(tokenizer: ThreadSafeTokenizer, *, sampling_settings: SamplingSettings) -> dict[int, float]:
    """Build logit bias map from text tokens to token IDs."""
    if not sampling_settings.logit_bias:
        return {}

    id_bias: dict[int, float] = {}
    for text, bias in sampling_settings.logit_bias.items():
        ids = tokenizer.encode_ids(text)
        if not ids:
            continue
        for token_id in ids:
            current = id_bias.get(token_id)
            value = float(bias)
            if current is None or value < current:
                id_bias[token_id] = value

    return id_bias


def _build_sampling_parameters(
    overrides: dict[str, float | int | bool],
    engine: Engine,
    tokenizer: ThreadSafeTokenizer,
    *,
    sampling_settings: SamplingSettings,
    session_settings: SessionSettings,
) -> object:
    """Build engine sampling parameters from resolved overrides."""
    logit_bias = _build_logit_bias_map(tokenizer, sampling_settings=sampling_settings)
    return engine.create_sampling_parameters(
        SamplingParametersRequest(
            temperature=float(overrides["temperature"]),
            top_p=float(overrides["top_p"]),
            top_k=int(overrides["top_k"]),
            min_p=float(overrides["min_p"]),
            repetition_penalty=float(overrides["repetition_penalty"]),
            presence_penalty=float(overrides["presence_penalty"]),
            frequency_penalty=float(overrides["frequency_penalty"]),
            maximum_tokens=session_settings.maximum_output_tokens,
            stop=list(sampling_settings.inference_stop),
            logit_bias=logit_bias or None,
        ),
    )


async def _stream_sanitized(
    stream: StreamController,
    *,
    is_sanitization_enabled: bool,
) -> AsyncGenerator[str, None]:
    """Yield stream chunks through the output sanitizer when enabled."""
    sanitizer = StreamingSanitizer() if is_sanitization_enabled else None
    async for chunk in stream:
        if sanitizer is None:
            yield chunk
            continue
        clean = sanitizer.push(chunk)
        if clean:
            yield clean
    if sanitizer is not None:
        tail = sanitizer.flush()
        if tail:
            yield tail


def build_sampling_overrides(
    overrides: dict[str, float | int | bool],
    *,
    sampling_settings: SamplingSettings,
) -> dict[str, float | int | bool]:
    """Resolve request sampling overrides against configured defaults."""
    return {
        "temperature": float(overrides.get("temperature", sampling_settings.temperature)),
        "top_p": float(overrides.get("top_p", sampling_settings.top_p)),
        "top_k": int(overrides.get("top_k", sampling_settings.top_k)),
        "min_p": float(overrides.get("min_p", sampling_settings.min_p)),
        "repetition_penalty": float(overrides.get("repetition_penalty", sampling_settings.repetition_penalty)),
        "presence_penalty": float(overrides.get("presence_penalty", sampling_settings.presence_penalty)),
        "frequency_penalty": float(overrides.get("frequency_penalty", sampling_settings.frequency_penalty)),
        "sanitize_output": bool(overrides.get("sanitize_output", False)),
    }


async def run_generation(request: GenerationRequest) -> AsyncGenerator[str, None]:
    """Stream generation with optional micro-coalescing."""
    request_id = request.request_id or f"generation-{uuid.uuid4()}"

    overrides = build_sampling_overrides(
        request.sampling_overrides or {},
        sampling_settings=request.sampling_settings,
    )
    parameters = _build_sampling_parameters(
        overrides,
        request.engine,
        request.tokenizer,
        sampling_settings=request.sampling_settings,
        session_settings=request.session_settings,
    )

    get_metrics().phase_latency.record(0.0, {"phase": "prompt_build"})
    resolved_prompt_token_count = request.prompt_token_count
    if resolved_prompt_token_count is None:
        resolved_prompt_token_count = len(request.tokenizer.encode_ids(request.prompt))
    if resolved_prompt_token_count > request.session_settings.maximum_context_length:
        message = (
            f"prompt exceeds exact context budget before engine call "
            f"({resolved_prompt_token_count} > {request.session_settings.maximum_context_length})"
        )
        raise ValueError(message)
    metrics = get_metrics()
    metrics.prompt_tokens.record(resolved_prompt_token_count)
    metrics.prompt_tokens_total.add(resolved_prompt_token_count)
    trace_span = trace.get_current_span()
    if trace_span.is_recording():
        trace_span.set_attribute("prompt_tokens", resolved_prompt_token_count)

    stream = StreamController(
        StreamConfig(
            session_id=request.state.session_id,
            request_id=request_id,
            prompt=request.prompt,
            sampling_parameters=parameters,
            engine=request.engine,
            timeout_seconds=float(request.timeout_settings.generation_timeout_seconds),
            flush_milliseconds=float(request.session_settings.stream_flush_milliseconds),
            cancellation_check=lambda: is_request_cancelled(request.state, request_id),
            count_completion_tokens=request.tokenizer.count,
        ),
    )
    async for chunk in _stream_sanitized(
        stream,
        is_sanitization_enabled=bool(overrides["sanitize_output"]),
    ):
        yield chunk


__all__ = ["GenerationRequest", "build_sampling_overrides", "run_generation"]
