"""Unit tests for backend-specific model validation."""

from __future__ import annotations

from src.scripts import validate
from typing import TYPE_CHECKING
from config.model.quantization import TRT_ENGINE, VLLM_ENGINE

if TYPE_CHECKING:
    import pytest


def test_vllm_model_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a vLLM-only source cannot cross the TensorRT boundary."""
    model = "example/vllm-only-model"
    monkeypatch.setattr(validate, "ALLOWED_VLLM_BASE_MODELS", [model])

    vllm_errors = validate.validate_models(model, VLLM_ENGINE, "fp8")
    trt_errors = validate.validate_models(model, TRT_ENGINE, "fp8")

    assert not vllm_errors
    assert any("MODEL must be allowlisted" in error for error in trt_errors)


def test_trt_model_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test a TensorRT-only source cannot cross the vLLM boundary."""
    model = "example/trt-only-model"
    monkeypatch.setattr(validate, "ALLOWED_TRT_BASE_MODELS", [model])

    trt_errors = validate.validate_models(model, TRT_ENGINE, "fp8")
    vllm_errors = validate.validate_models(model, VLLM_ENGINE, "fp8")

    assert not trt_errors
    assert any("MODEL must be allowlisted" in error for error in vllm_errors)
