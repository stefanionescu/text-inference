"""Regression coverage for optional TorchVision import failures."""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING
import subprocess

if TYPE_CHECKING:
    from pathlib import Path


CUDA_MISMATCH_EXIT_CODE = 42


def test_cuda_import_failure(tmp_path: Path) -> None:
    """Retain the import error after Python clears the exception target.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    (tmp_path / "torch.py").write_text(
        'from types import SimpleNamespace\n__version__ = "test"\nversion = SimpleNamespace(cuda="12.0")\n',
        encoding="utf-8",
    )
    (tmp_path / "torchvision.py").write_text(
        'raise RuntimeError("PyTorch and torchvision were compiled with different CUDA major versions")\n',
        encoding="utf-8",
    )
    result = subprocess.run(
        [sys.executable, "-m", "src.scripts.guard"],
        env={**os.environ, "PYTHONPATH": str(tmp_path)},
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == CUDA_MISMATCH_EXIT_CODE
    assert "different CUDA major versions" in result.stdout
    assert "torch==test (CUDA 12.0)" in result.stdout
    assert result.stderr == ""
