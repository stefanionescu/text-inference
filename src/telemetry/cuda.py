"""Torch-backed GPU telemetry integration."""

from __future__ import annotations

import torch
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .gpu import GPUProvider


class _TorchGPUProvider:
    """Expose Torch CUDA measurements through the telemetry protocol."""

    def is_available(self) -> bool:
        """Return whether Torch can access CUDA."""
        return bool(torch.cuda.is_available())

    def device_count(self) -> int:
        """Return the visible CUDA device count."""
        return int(torch.cuda.device_count())

    def allocated_memory_bytes(self, device_id: int) -> int:
        """Return allocated CUDA memory for one device."""
        return int(torch.cuda.memory_allocated(device_id))

    def total_memory_bytes(self, device_id: int) -> int:
        """Return total CUDA memory for one device."""
        return int(torch.cuda.get_device_properties(device_id).total_memory)

    def utilization_percentage(self, device_id: int) -> float:
        """Return CUDA utilization for one device."""
        return float(torch.cuda.utilization(device_id))


GPU_PROVIDER: GPUProvider = _TorchGPUProvider()


__all__ = ["GPU_PROVIDER"]
