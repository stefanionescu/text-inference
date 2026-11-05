"""Regression coverage for the public TRT cache command."""

from __future__ import annotations

from unittest.mock import Mock

import pytest

from src.quantization import trt


@pytest.mark.parametrize("is_forced", [False, True])
def test_cache_command_rebuilds(
    *,
    is_forced: bool,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Both cache paths accept argparse output and select rebuilding correctly."""
    monkeypatch.setattr(trt, "_build_request", Mock(return_value=object()))
    monkeypatch.setattr(trt, "cache_matches", Mock(return_value=False))
    arguments = [
        "cache",
        "--source-model",
        "example/model",
        "--source-dir",
        ".",
        "--source-revision",
        "revision",
        "--checkpoint-dir",
        ".",
        "--format",
        "int4_awq",
        "--calibration-dataset",
        "example",
        "--calibration-samples",
        "1",
        "--calibration-sequence-length",
        "128",
        "--awq-block-size",
        "128",
        "--kv-cache-format",
        "fp8",
        "--gpu-max-mem-percentage",
        "0.8",
        "--sequential-device-map",
        "0",
        "--modelopt-repository",
        ".",
    ]
    if is_forced:
        arguments.append("--force-rebuild")
    assert trt.main(arguments) == 0
    assert capsys.readouterr().out == "rebuild\n"
