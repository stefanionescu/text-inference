"""PyTorch/TorchVision CUDA version mismatch detection.

Detects when PyTorch and TorchVision were compiled against different CUDA
major versions, which causes RuntimeError on import. Shell scripts use this
to proactively uninstall mismatched packages before reinstalling.
"""

from __future__ import annotations

import sys
import importlib.util

try:
    import torch as _torch
except (ImportError, OSError, RuntimeError):
    _torch = None

try:
    import torchvision as _torchvision
except (ImportError, OSError, RuntimeError) as _torchvision_import_error:
    _torchvision = None
else:
    _torchvision_import_error = None

# Exit code indicating CUDA mismatch was detected
EXIT_CODE_MISMATCH = 42


def detect_cuda_mismatch() -> tuple[bool, str]:
    """Detect PyTorch/TorchVision CUDA version mismatch.

    Returns:
        Tuple of ``(has_mismatch, message)``.
        - has_mismatch: True if packages have incompatible CUDA versions.
        - message: Error message with fragments, empty if no mismatch.

    """
    # Check if torch is installed
    torch_spec = importlib.util.find_spec("torch")
    if torch_spec is None or _torch is None:
        return False, ""

    # Check if torchvision is installed
    vision_spec = importlib.util.find_spec("torchvision")
    if vision_spec is None:
        return False, ""

    has_mismatch = False
    mismatch_message = ""
    if _torchvision is None and _torchvision_import_error is not None:
        message = str(_torchvision_import_error).strip()
        needle = "PyTorch and torchvision were compiled with different CUDA major versions"
        if needle in message:
            # Build detailed message
            torch_version = getattr(_torch, "__version__", "")
            torch_cuda_version = (getattr(_torch.version, "cuda", "") or "").strip()
            mismatch_message = message
            if torch_version:
                summary = f"torch=={torch_version}"
                if torch_cuda_version:
                    summary += f" (CUDA {torch_cuda_version})"
                mismatch_message = f"{message}\n{summary}"
            has_mismatch = True

    return has_mismatch, mismatch_message


if __name__ == "__main__":
    # CLI interface for shell scripts
    has_mismatch, message = detect_cuda_mismatch()

    if has_mismatch:
        if message:
            sys.stdout.write(str(message) + "\n")
        sys.exit(EXIT_CODE_MISMATCH)

    sys.exit(0)
