"""Unit tests for quantization detection."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from config.model.quantization import QUANTIZATIONS_BY_ENGINE
from src.quantization.detection import detect_format
from src.quantization.checkpoint import validate_checkpoint

if TYPE_CHECKING:
    from pathlib import Path


def test_detects_nvfp4(tmp_path: Path) -> None:
    """Test ModelOpt NVFP4 metadata is detected.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    config = {"quantization_config": {"quant_method": "modelopt", "quant_algo": "NVFP4"}}
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")

    assert detect_format(str(tmp_path), "trt") == "nvfp4"


def test_detects_modelopt_nvfp(tmp_path: Path) -> None:
    """Test ModelOpt's W4A16 NVFP4 label maps to the NVFP4 format.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    config = {"quantization_config": {"quant_method": "modelopt", "quant_algo": "W4A16_NVFP4"}}
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")

    assert detect_format(str(tmp_path), "trt") == "nvfp4"


def test_detects_standalone_metadata(tmp_path: Path) -> None:
    """Test standalone quantization metadata is detected.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    declared_format = "gptq"
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    (tmp_path / "quantization_config.json").write_text(
        json.dumps({"quant_method": declared_format}),
        encoding="utf-8",
    )

    assert detect_format(str(tmp_path), "vllm") == declared_format


def test_detects_vllm_int(tmp_path: Path) -> None:
    """Test vLLM accepts INT8 W8A8 through its checkpoint format.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    config = {
        "quantization_config": {
            "quant_method": "compressed-tensors",
            "config_groups": {
                "group_0": {
                    "weights": {"num_bits": 8, "type": "int"},
                    "input_activations": {"num_bits": 8, "type": "int"},
                },
            },
        },
    }
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")

    assert detect_format(str(tmp_path), "vllm") == "compressed-tensors"


def test_detects_earlier_int(tmp_path: Path) -> None:
    """Test unsupported TRT INT8 metadata remains diagnosable.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    config = {
        "quantization_config": {
            "quant_method": "modelopt",
            "quant_algo": "W8A8_SQ_PER_CHANNEL",
        },
    }
    (tmp_path / "config.json").write_text(json.dumps(config), encoding="utf-8")

    assert detect_format(str(tmp_path), "trt") == "int8_sq"


def test_int_vllm_support(tmp_path: Path) -> None:
    """Test TRT rejects INT8 while vLLM retains compressed-tensors support.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    assert "compressed-tensors" in QUANTIZATIONS_BY_ENGINE["vllm"]
    assert "int8_sq" not in QUANTIZATIONS_BY_ENGINE["trt"]

    with pytest.raises(ValueError, match="not supported by trt"):
        validate_checkpoint(tmp_path / "legacy-int8", "trt", "int8_sq")


def test_rejects_metadata_conflicts(tmp_path: Path) -> None:
    """Test inconsistent exact metadata fails explicitly.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    (tmp_path / "config.json").write_text(
        json.dumps({"quantization_config": {"quant_method": "awq"}}),
        encoding="utf-8",
    )
    (tmp_path / "quant_config.json").write_text(
        json.dumps({"quant_method": "gptq"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Conflicting quantization formats"):
        detect_format(str(tmp_path), "vllm")
