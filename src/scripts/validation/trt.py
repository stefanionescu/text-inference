"""Validate the TensorRT-LLM 1.3.0rc20 runtime contract."""

from __future__ import annotations

import sys
import ctypes
import ctypes.util
import tensorrt_llm
from mpi4py import MPI
from importlib.metadata import version
from config.model.trt import TRT_VERSION
from cuda.bindings import runtime as cuda_runtime
from src.scripts.cuda import read_cuda_driver_version


def main() -> int:
    """Validate every required TensorRT-LLM runtime dependency."""
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    python_library = ctypes.util.find_library(f"python{python_version}")
    if python_library is None:
        message = f"libpython{python_version} is required"
        raise RuntimeError(message)
    ctypes.CDLL(python_library)

    error_code, _driver_version = read_cuda_driver_version(cuda_runtime.cudaDriverGetVersion)
    if error_code != 0:
        message = f"cudaDriverGetVersion failed with error {error_code}"
        raise RuntimeError(message)

    MPI.Get_version()

    installed_version = version("tensorrt-llm")
    if installed_version != TRT_VERSION or tensorrt_llm.__version__ != TRT_VERSION:
        message = f"TensorRT-LLM {TRT_VERSION} is required, installed {installed_version}"
        raise RuntimeError(message)

    sys.stdout.write(f"[trt] TensorRT-LLM {installed_version} runtime validated\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
