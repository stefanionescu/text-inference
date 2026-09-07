"""Span context managers for session, request, and generation tracing."""

from __future__ import annotations

from opentelemetry import trace
from typing import TYPE_CHECKING
from dataclasses import dataclass
from contextlib import contextmanager
from src.runtime.environment import read_environment_text
from config.runtime.telemetry import OTEL_RESOURCE_NAME, SPAN_GENERATION, SPAN_REQUEST, SPAN_SESSION

if TYPE_CHECKING:
    from collections.abc import Generator


@dataclass(frozen=True, slots=True)
class RequestSpanAttributes:
    """Attributes for a request span."""

    request_id: str
    session_id: str = ""
    client_id: str = ""
    model: str = ""
    prompt_tokens: int = 0
    temperature: float = 0.0


def _resource_name() -> str:
    """Return the configured tracing service name."""
    return read_environment_text("OTEL_RESOURCE_NAME", OTEL_RESOURCE_NAME)


@contextmanager
def session_span(*, client_id: str) -> Generator[trace.Span, None, None]:
    """Outermost span wrapping the entire WebSocket connection."""
    with trace.get_tracer(_resource_name()).start_as_current_span(
        SPAN_SESSION,
        attributes={"client.id": client_id},
    ) as span:
        yield span


@contextmanager
def request_span(span_attributes: RequestSpanAttributes) -> Generator[trace.Span, None, None]:
    """Per-message/turn span."""
    attributes: dict[str, str | int | float] = {"request.id": span_attributes.request_id}
    if span_attributes.session_id:
        attributes["session.id"] = span_attributes.session_id
    if span_attributes.client_id:
        attributes["client.id"] = span_attributes.client_id
    if span_attributes.model:
        attributes["model"] = span_attributes.model
    if span_attributes.prompt_tokens:
        attributes["prompt_tokens"] = span_attributes.prompt_tokens
    if span_attributes.temperature:
        attributes["temperature"] = span_attributes.temperature
    with trace.get_tracer(_resource_name()).start_as_current_span(SPAN_REQUEST, attributes=attributes) as span:
        yield span


@contextmanager
def generation_span(
    *,
    engine_type: str = "",
    completion_tokens: int = 0,
    finish_reason: str = "",
) -> Generator[trace.Span, None, None]:
    """Engine generation call span."""
    attributes: dict[str, str] = {}
    if engine_type:
        attributes["engine.type"] = engine_type
    with trace.get_tracer(_resource_name()).start_as_current_span(SPAN_GENERATION, attributes=attributes) as span:
        yield span
        if completion_tokens:
            span.set_attribute("completion_tokens", completion_tokens)
        if finish_reason:
            span.set_attribute("finish_reason", finish_reason)


__all__ = ["RequestSpanAttributes", "generation_span", "request_span", "session_span"]
