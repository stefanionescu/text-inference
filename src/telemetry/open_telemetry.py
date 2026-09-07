"""TracerProvider + MeterProvider setup for Axiom via OpenTelemetry."""

from __future__ import annotations

import uuid
import socket
import logging
from dataclasses import dataclass
from opentelemetry import metrics, trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from src.runtime.environment import read_environment_integer, read_environment_text
from opentelemetry.exporter.otlp.proto.http.metric_exporter import OTLPMetricExporter
from config.runtime.telemetry import (
    AXIOM_DATASET,
    CLOUD_PLATFORM,
    AXIOM_API_TOKEN,
    AXIOM_ENVIRONMENT,
    OTEL_RESOURCE_NAME,
    AXIOM_TRACES_ENDPOINT,
    AXIOM_METRICS_ENDPOINT,
    OTEL_TRACES_BATCH_SIZE,
    OTEL_TRACES_EXPORT_INTERVAL_MILLISECONDS,
    OTEL_METRICS_EXPORT_INTERVAL_MILLISECONDS,
)

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class _OpenTelemetryState:
    """Process-wide OpenTelemetry provider state."""

    tracer_provider: TracerProvider | None = None
    meter_provider: MeterProvider | None = None


_OPEN_TELEMETRY_STATE = _OpenTelemetryState()


def _build_resource() -> Resource:
    """Build OpenTelemetry resource attributes for this process."""
    attributes: dict[str, str] = {
        "service.name": read_environment_text("OTEL_RESOURCE_NAME", OTEL_RESOURCE_NAME),
        "deployment.environment": read_environment_text("AXIOM_ENVIRONMENT", AXIOM_ENVIRONMENT),
        "host.name": socket.gethostname(),
        "service.instance.id": uuid.uuid4().hex[:12],
    }
    cloud_platform = read_environment_text("CLOUD_PLATFORM", CLOUD_PLATFORM)
    if cloud_platform:
        attributes["cloud.platform"] = cloud_platform
    return Resource.create(attributes)


def _axiom_headers() -> dict[str, str]:
    """Build headers for Axiom OTLP exporters."""
    return {
        "Authorization": f"Bearer {read_environment_text('AXIOM_API_TOKEN', AXIOM_API_TOKEN)}",
        "X-Axiom-Dataset": read_environment_text("AXIOM_DATASET", AXIOM_DATASET),
    }


def initialize_open_telemetry() -> None:
    """Create and register global TracerProvider + MeterProvider. Idempotent."""
    if _OPEN_TELEMETRY_STATE.tracer_provider is not None:
        return

    resource = _build_resource()
    headers = _axiom_headers()

    # Traces
    traces_endpoint = read_environment_text("AXIOM_TRACES_ENDPOINT", AXIOM_TRACES_ENDPOINT)
    metrics_endpoint = read_environment_text("AXIOM_METRICS_ENDPOINT", AXIOM_METRICS_ENDPOINT)
    span_exporter = OTLPSpanExporter(endpoint=traces_endpoint, headers=headers)
    span_batcher = BatchSpanProcessor(
        span_exporter,
        max_export_batch_size=max(1, read_environment_integer("OTEL_TRACES_BATCH_SIZE", OTEL_TRACES_BATCH_SIZE)),
        schedule_delay_millis=max(
            1000,
            read_environment_integer(
                "OTEL_TRACES_EXPORT_INTERVAL_MILLISECONDS",
                OTEL_TRACES_EXPORT_INTERVAL_MILLISECONDS,
            ),
        ),
    )
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(span_batcher)
    trace.set_tracer_provider(tracer_provider)
    _OPEN_TELEMETRY_STATE.tracer_provider = tracer_provider

    # Metrics
    metric_exporter = OTLPMetricExporter(endpoint=metrics_endpoint, headers=headers)
    metric_reader = PeriodicExportingMetricReader(
        metric_exporter,
        export_interval_millis=max(
            1000,
            read_environment_integer(
                "OTEL_METRICS_EXPORT_INTERVAL_MILLISECONDS",
                OTEL_METRICS_EXPORT_INTERVAL_MILLISECONDS,
            ),
        ),
    )
    meter_provider = MeterProvider(resource=resource, metric_readers=[metric_reader])
    metrics.set_meter_provider(meter_provider)
    _OPEN_TELEMETRY_STATE.meter_provider = meter_provider

    logger.info("OTel initialized: traces=%s metrics=%s", traces_endpoint, metrics_endpoint)


def shutdown_open_telemetry() -> None:
    """Flush and shutdown both providers. Idempotent."""
    if _OPEN_TELEMETRY_STATE.tracer_provider is not None:
        _OPEN_TELEMETRY_STATE.tracer_provider.force_flush()
        _OPEN_TELEMETRY_STATE.tracer_provider.shutdown()
        _OPEN_TELEMETRY_STATE.tracer_provider = None
    if _OPEN_TELEMETRY_STATE.meter_provider is not None:
        _OPEN_TELEMETRY_STATE.meter_provider.force_flush()
        _OPEN_TELEMETRY_STATE.meter_provider.shutdown()
        _OPEN_TELEMETRY_STATE.meter_provider = None


__all__ = ["initialize_open_telemetry", "shutdown_open_telemetry"]
