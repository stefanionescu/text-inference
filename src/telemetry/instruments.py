"""MetricInstruments registry — typed accessors for all OTel instruments."""

from __future__ import annotations

from typing import TYPE_CHECKING
import logging
from dataclasses import dataclass

from opentelemetry import metrics

from src.runtime.environment import read_environment_text
from config.runtime.telemetry import (
    METRIC_TTFT,
    OTEL_RESOURCE_NAME,
    METRIC_ERRORS_TOTAL,
    METRIC_PHASE_LATENCY,
    METRIC_PROMPT_TOKENS,
    METRIC_TOKEN_LATENCY,
    METRIC_REQUESTS_TOTAL,
    METRIC_REQUEST_LATENCY,
    METRIC_STARTUP_DURATION,
    METRIC_COMPLETION_TOKENS,
    METRIC_ACTIVE_CONNECTIONS,
    METRIC_ACTIVE_GENERATIONS,
    METRIC_CACHE_RESETS_TOTAL,
    METRIC_CANCELLATION_TOTAL,
    METRIC_EARLY_CANCEL_TOTAL,
    METRIC_PHASE_ERRORS_TOTAL,
    METRIC_CONNECTION_DURATION,
    METRIC_PROMPT_TOKENS_TOTAL,
    METRIC_SESSION_CHURN_TOTAL,
    METRIC_TOKENS_GENERATED_TOTAL,
    METRIC_WEBSOCKET_SEND_LATENCY,
    METRIC_CACHE_RESET_SKIPS_TOTAL,
    METRIC_GENERATIONS_PER_SESSION,
    METRIC_EMPTY_MODEL_OUTPUT_TOTAL,
    METRIC_CONNECTION_SEMAPHORE_WAIT,
    METRIC_TIMEOUT_DISCONNECTS_TOTAL,
    METRIC_CACHE_RESET_FAILURES_TOTAL,
    METRIC_CONNECTIONS_REJECTED_TOTAL,
    METRIC_DISCONNECT_MID_STREAM_TOTAL,
    METRIC_RATE_LIMIT_VIOLATIONS_TOTAL,
    METRIC_ENGINE_ABORT_RETRYABLE_TOTAL,
)

from .gpu import register_gpu_observables

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .gpu import GPUProvider


def _resource_name() -> str:
    """Return the configured OpenTelemetry service name."""
    return read_environment_text("OTEL_RESOURCE_NAME", OTEL_RESOURCE_NAME)


def _histogram(meter: metrics.Meter, spec: tuple[str, str, str]) -> metrics.Histogram:
    """Create a histogram from a metric spec."""
    name, unit, description = spec
    return meter.create_histogram(name, unit=unit, description=description)


def _counter(meter: metrics.Meter, spec: tuple[str, str, str]) -> metrics.Counter:
    """Create a counter from a metric spec."""
    name, unit, description = spec
    return meter.create_counter(name, unit=unit, description=description)


def _updown(meter: metrics.Meter, spec: tuple[str, str, str]) -> metrics.UpDownCounter:
    """Create an up-down counter from a metric spec."""
    name, unit, description = spec
    return meter.create_up_down_counter(name, unit=unit, description=description)


class MetricInstruments:
    """Holds all OTel metric instruments created from config specs."""

    __slots__ = (
        "active_connections",
        "active_generations",
        "cache_reset_failures_total",
        "cache_reset_skips_total",
        "cache_resets_total",
        "cancellation_total",
        "completion_tokens",
        "connection_duration",
        "connection_semaphore_wait",
        "connections_rejected_total",
        "disconnect_mid_stream_total",
        "early_cancel_total",
        "empty_model_output_total",
        "engine_abort_retryable_total",
        "errors_total",
        "generations_per_session",
        "phase_errors_total",
        "phase_latency",
        "prompt_tokens",
        "prompt_tokens_total",
        "rate_limit_violations_total",
        "request_latency",
        "requests_total",
        "session_churn_total",
        "startup_duration",
        "timeout_disconnects_total",
        "token_latency",
        "tokens_generated_total",
        "ttft",
        "websocket_send_latency",
    )

    def __init__(self, meter: metrics.Meter) -> None:
        """Initialize all metric instruments from one meter."""
        self._initialize_histograms(meter)
        self._initialize_counters(meter)
        self._initialize_updown_counters(meter)

    def _initialize_histograms(self, meter: metrics.Meter) -> None:
        """Initialize request and lifecycle duration histograms."""
        self.ttft = _histogram(meter, METRIC_TTFT)
        self.request_latency = _histogram(meter, METRIC_REQUEST_LATENCY)
        self.token_latency = _histogram(meter, METRIC_TOKEN_LATENCY)
        self.connection_duration = _histogram(meter, METRIC_CONNECTION_DURATION)
        self.connection_semaphore_wait = _histogram(meter, METRIC_CONNECTION_SEMAPHORE_WAIT)
        self.prompt_tokens = _histogram(meter, METRIC_PROMPT_TOKENS)
        self.completion_tokens = _histogram(meter, METRIC_COMPLETION_TOKENS)
        self.generations_per_session = _histogram(meter, METRIC_GENERATIONS_PER_SESSION)
        self.startup_duration = _histogram(meter, METRIC_STARTUP_DURATION)
        self.phase_latency = _histogram(meter, METRIC_PHASE_LATENCY)
        self.websocket_send_latency = _histogram(meter, METRIC_WEBSOCKET_SEND_LATENCY)

    def _initialize_counters(self, meter: metrics.Meter) -> None:
        """Initialize cumulative event counters."""
        self.requests_total = _counter(meter, METRIC_REQUESTS_TOTAL)
        self.tokens_generated_total = _counter(meter, METRIC_TOKENS_GENERATED_TOTAL)
        self.prompt_tokens_total = _counter(meter, METRIC_PROMPT_TOKENS_TOTAL)
        self.connections_rejected_total = _counter(meter, METRIC_CONNECTIONS_REJECTED_TOTAL)
        self.session_churn_total = _counter(meter, METRIC_SESSION_CHURN_TOTAL)
        self.cancellation_total = _counter(meter, METRIC_CANCELLATION_TOTAL)
        self.errors_total = _counter(meter, METRIC_ERRORS_TOTAL)
        self.timeout_disconnects_total = _counter(meter, METRIC_TIMEOUT_DISCONNECTS_TOTAL)
        self.rate_limit_violations_total = _counter(meter, METRIC_RATE_LIMIT_VIOLATIONS_TOTAL)
        self.cache_resets_total = _counter(meter, METRIC_CACHE_RESETS_TOTAL)
        self.cache_reset_failures_total = _counter(meter, METRIC_CACHE_RESET_FAILURES_TOTAL)
        self.cache_reset_skips_total = _counter(meter, METRIC_CACHE_RESET_SKIPS_TOTAL)
        self.phase_errors_total = _counter(meter, METRIC_PHASE_ERRORS_TOTAL)
        self.disconnect_mid_stream_total = _counter(meter, METRIC_DISCONNECT_MID_STREAM_TOTAL)
        self.early_cancel_total = _counter(meter, METRIC_EARLY_CANCEL_TOTAL)
        self.empty_model_output_total = _counter(meter, METRIC_EMPTY_MODEL_OUTPUT_TOTAL)
        self.engine_abort_retryable_total = _counter(meter, METRIC_ENGINE_ABORT_RETRYABLE_TOTAL)

    def _initialize_updown_counters(self, meter: metrics.Meter) -> None:
        """Initialize gauges represented by up-down counters."""
        self.active_connections = _updown(meter, METRIC_ACTIVE_CONNECTIONS)
        self.active_generations = _updown(meter, METRIC_ACTIVE_GENERATIONS)


@dataclass(slots=True)
class _MetricState:
    """Process-wide metric instrument state."""

    instruments: MetricInstruments | None = None


_METRIC_STATE = _MetricState()


def get_metrics() -> MetricInstruments:
    """Return the global MetricInstruments (no-op meter if OTel not initialized)."""
    if _METRIC_STATE.instruments is None:
        meter = metrics.get_meter(_resource_name())
        _METRIC_STATE.instruments = MetricInstruments(meter)
    return _METRIC_STATE.instruments


def initialize_metrics(gpu_provider: GPUProvider | None = None) -> None:
    """Create MetricInstruments from the global meter and register GPU observables."""
    meter = metrics.get_meter(_resource_name())
    _METRIC_STATE.instruments = MetricInstruments(meter)
    if gpu_provider is not None:
        register_gpu_observables(meter, gpu_provider)
    logger.info("Telemetry metrics initialized")


__all__ = ["MetricInstruments", "get_metrics", "initialize_metrics"]
