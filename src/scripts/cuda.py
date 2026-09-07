"""Typed CUDA runtime result handling."""

from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from collections.abc import Sequence

CUDA_RESULT_LENGTH = 2


class CudaDriverVersionQuery(Protocol):
    """Callable CUDA driver version query."""

    def __call__(self) -> Sequence[object]:
        """Return the CUDA driver query result."""
        raise NotImplementedError


def read_cuda_driver_version(query_driver_version: CudaDriverVersionQuery) -> tuple[int, int]:
    """Call CUDA runtime driver version and validate its result shape."""
    result = query_driver_version()
    if len(result) != CUDA_RESULT_LENGTH:
        message = "cudaDriverGetVersion returned an invalid result"
        raise RuntimeError(message)
    error_code = result[0]
    driver_version = result[1]
    if not isinstance(error_code, int) or not isinstance(driver_version, int):
        message = "cudaDriverGetVersion returned non-integer values"
        raise TypeError(message)
    return error_code, driver_version


__all__ = ["CudaDriverVersionQuery", "read_cuda_driver_version"]
