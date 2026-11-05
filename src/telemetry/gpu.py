"""GPU observable gauges (multi-device) for OpenTelemetry."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol
import logging

from opentelemetry.metrics import Observation

from config.runtime.telemetry import (
    METRIC_GPU_MEMORY_FREE,
    METRIC_GPU_MEMORY_USED,
    METRIC_GPU_UTILIZATION,
    METRIC_GPU_MEMORY_TOTAL,
)

if TYPE_CHECKING:
    from opentelemetry.metrics import Meter

logger = logging.getLogger(__name__)


class GPUProvider(Protocol):
    """GPU measurements required by OpenTelemetry observables."""

    def is_available(self) -> bool:
        """Return whether GPU telemetry is available.

        Returns:
            True when the provider can read GPU metrics; otherwise the gauges report nothing.

        Raises:
            NotImplementedError: This stub always raises; a provider answers whether GPUs are visible.

        """
        raise NotImplementedError

    def device_count(self) -> int:
        """Return the number of visible GPU devices.

        Returns:
            Number of devices that the gauges iterate.

        Raises:
            NotImplementedError: This stub always raises; a provider counts the devices.

        """
        raise NotImplementedError

    def allocated_memory_bytes(self, device_id: int) -> int:
        """Return allocated bytes for one device.

        Args:
            device_id: Index of the GPU to read.

        Returns:
            Bytes currently allocated on that GPU.

        Raises:
            NotImplementedError: This stub always raises; a provider reads the allocation.

        """
        raise NotImplementedError(device_id)

    def total_memory_bytes(self, device_id: int) -> int:
        """Return total bytes for one device.

        Args:
            device_id: Index of the GPU whose capacity to read.

        Returns:
            Memory capacity of that GPU in bytes.

        Raises:
            NotImplementedError: This stub always raises; a provider reads the capacity.

        """
        raise NotImplementedError(device_id)

    def utilization_percentage(self, device_id: int) -> float:
        """Return utilization percentage for one device.

        Args:
            device_id: Index of the GPU whose load to read.

        Returns:
            Load of that GPU as a percentage.

        Raises:
            NotImplementedError: This stub always raises; a provider reads the load.

        """
        raise NotImplementedError(device_id)


def _memory_observation(
    provider: GPUProvider,
    metric_kind: str,
    device_id: int,
    attributes: dict[str, str],
) -> Observation | None:
    """Build a GPU memory observation for one device.

    Args:
        provider: Source of GPU readings.
        metric_kind: `memory_allocated`, `memory_free`, or `memory_total`.
        device_id: GPU index to read.
        attributes: Telemetry attributes to attach.

    Returns:
        The observation, or None for any other metric kind.

    """
    memory_bytes: int | None = None
    if metric_kind == "memory_allocated":
        memory_bytes = provider.allocated_memory_bytes(device_id)
    elif metric_kind == "memory_free":
        memory_bytes = provider.total_memory_bytes(device_id) - provider.allocated_memory_bytes(device_id)
    elif metric_kind == "memory_total":
        memory_bytes = provider.total_memory_bytes(device_id)
    return Observation(memory_bytes, attributes) if memory_bytes is not None else None


def _utilization_observation(
    provider: GPUProvider,
    device_id: int,
    attributes: dict[str, str],
) -> Observation | None:
    """Build a GPU utilization observation for one device.

    Args:
        provider: Source of GPU readings.
        device_id: GPU index to read.
        attributes: Telemetry attributes to attach.

    Returns:
        The observation, or None when the provider read fails.

    """
    try:
        gpu_utilization = provider.utilization_percentage(device_id)
    except (OSError, RuntimeError, ValueError):
        logger.debug("failed to read GPU utilization for device %s", device_id, exc_info=True)
        return None
    return Observation(float(gpu_utilization), attributes)


def _device_observation(provider: GPUProvider, metric_kind: str, device_id: int) -> Observation | None:
    """Build one GPU observation for a metric kind and device.

    Args:
        provider: Source of GPU readings.
        metric_kind: `utilization` or a memory metric kind.
        device_id: GPU index to read, recorded as the `gpu.device.id` attribute.

    Returns:
        The observation, or None when no reading exists.

    """
    attributes = {"gpu.device.id": str(device_id)}
    if metric_kind == "utilization":
        return _utilization_observation(provider, device_id, attributes)
    return _memory_observation(provider, metric_kind, device_id, attributes)


def _read_gpu_observations(provider: GPUProvider, metric_kind: str) -> list[Observation]:
    """Read all GPU observations for one metric kind.

    Args:
        provider: Source of GPU readings.
        metric_kind: Metric kind to read from every device.

    Returns:
        One observation per device with a reading; empty when GPUs are unavailable.

    """
    if not provider.is_available():
        return []
    return [
        observation
        for device_id in range(provider.device_count())
        if (observation := _device_observation(provider, metric_kind, device_id)) is not None
    ]


def register_gpu_observables(meter: Meter, provider: GPUProvider) -> None:
    """Register all GPU observable gauges on the given meter.

    Args:
        meter: OpenTelemetry meter that creates the instruments.
        provider: Source of GPU readings.

    """
    metric_name, unit, description = METRIC_GPU_MEMORY_USED
    meter.create_observable_gauge(
        metric_name,
        callbacks=[lambda _options=None: _read_gpu_observations(provider, "memory_allocated")],
        unit=unit,
        description=description,
    )

    metric_name, unit, description = METRIC_GPU_MEMORY_FREE
    meter.create_observable_gauge(
        metric_name,
        callbacks=[lambda _options=None: _read_gpu_observations(provider, "memory_free")],
        unit=unit,
        description=description,
    )

    metric_name, unit, description = METRIC_GPU_MEMORY_TOTAL
    meter.create_observable_gauge(
        metric_name,
        callbacks=[lambda _options=None: _read_gpu_observations(provider, "memory_total")],
        unit=unit,
        description=description,
    )

    metric_name, unit, description = METRIC_GPU_UTILIZATION
    meter.create_observable_gauge(
        metric_name,
        callbacks=[lambda _options=None: _read_gpu_observations(provider, "utilization")],
        unit=unit,
        description=description,
    )


__all__ = ["GPUProvider", "register_gpu_observables"]
