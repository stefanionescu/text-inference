"""GPU memory and architecture configuration.

The remaining memory is reserved for:
    - CUDA runtime overhead
    - Memory fragmentation
    - Temporary allocations

Environment Variables:
    GPU_MEMORY_FRACTION: Fraction of GPU memory for the engine (0.0-1.0)
    KV_DTYPE: KV cache payload type accepted by vLLM
    GPU_SM_ARCH: GPU SM architecture for FP8 support detection
"""

from __future__ import annotations

# ============================================================================
# GPU Memory Allocation
# ============================================================================
# The engine (vLLM/TRT) uses most GPU memory for model weights and KV cache.

GPU_MEMORY_FRACTION = 0.90

# ============================================================================
# KV Cache Configuration
# ============================================================================
# KV cache stores attention states for prefix caching and generation.
# FP8 reduces memory by 50% vs FP16 but requires Ada/Hopper GPUs.

KV_DTYPE = "auto"
KV_DTYPES: set[str] = {"auto", "fp8"}

# ============================================================================
# GPU Architecture Detection
# ============================================================================
# SM architecture determines FP8 support:
# - sm80 (A100): No native FP8; vLLM supports INT8 W8A8/SmoothQuant
# - sm89 (L40S, RTX 4090): Native FP8 support
# - sm90 (H100): Native FP8 support with higher throughput

GPU_SM_ARCH = ""  # e.g., "sm89", "sm90"

__all__ = [
    "GPU_MEMORY_FRACTION",
    "GPU_SM_ARCH",
    "KV_DTYPE",
    "KV_DTYPES",
]
