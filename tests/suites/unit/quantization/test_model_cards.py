"""Unit tests for detailed quantized-checkpoint model cards."""

from __future__ import annotations

from typing import TYPE_CHECKING
from src.hf.license import LicenseMetadata
from src.hf.trt import build_model_card as build_trt_card
from src.hf.vllm import build_model_card as build_vllm_card

if TYPE_CHECKING:
    import pytest


def _build_license(
    model_name: str,
    source_kind: str,
    source_revision: str,
    *,
    hf_token: str | None,
) -> LicenseMetadata:
    """Return scenario license metadata."""
    del model_name, source_kind, source_revision, hf_token
    return LicenseMetadata(
        identifier="scenario-license",
        name="Scenario License",
        link="https://example.invalid/license",
    )


def _build_metadata(engine: str, quantization_format: str) -> dict[str, object]:
    """Build scenario quantization provenance."""
    return {
        "schema_version": 1,
        "cache_key": "scenario-cache-key",
        "engine": engine,
        "format": quantization_format,
        "source": {
            "kind": "hub",
            "model": "example/base-model",
            "requested_revision": "main",
            "resolved_revision": "a" * 40,
        },
        "created_at": "2030-01-01T00:00:00Z",
        "environment": {
            "gpu_name": "Scenario GPU",
            "sm_arch": "sm90",
            "cuda_version": "13.1",
            "python_version": "3.12",
        },
    }


def test_vllm_card_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the vLLM card includes quantization and calibration details."""
    monkeypatch.setattr("src.hf.model_card.read_license", _build_license)
    metadata = _build_metadata("vllm", "compressed-tensors")
    metadata.update(
        {
            "quantizer": {"name": "llmcompressor", "version": "scenario-version"},
            "quantization": {
                "model_family": "moe",
                "scheme": "scenario-scheme",
                "weight_bits": 4,
                "group_size": 128,
                "symmetric": True,
                "targets": ["Linear"],
                "ignored_modules": ["lm_head"],
            },
            "calibration": {
                "dataset": "scenario-dataset",
                "num_samples": 23,
                "sequence_length": 321,
                "batch_size": 2,
                "pipeline": "sequential",
                "moe_calibrate_all_experts": True,
            },
            "checkpoint_quantization_config": {
                "quant_method": "compressed-tensors",
            },
        },
    )

    card = build_vllm_card(metadata, "example/quantized-model", hf_token=None)

    assert "Scenario License" in card
    assert "scenario-dataset" in card
    assert "all experts" in card
    assert "a" * 40 in card


def test_trt_card_provenance(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test the TRT card includes ModelOpt checkpoint provenance."""
    monkeypatch.setattr("src.hf.model_card.read_license", _build_license)
    metadata = _build_metadata("trt", "int4_awq")
    metadata.update(
        {
            "quantizer": {
                "name": "NVIDIA Model Optimizer",
                "version": "scenario-version",
                "revision": "scenario-revision",
            },
            "quantization": {
                "qformat": "int4_awq",
                "kv_cache_qformat": "none",
                "awq_block_size": 64,
            },
            "calibration": {
                "dataset": "scenario-dataset",
                "num_samples": 31,
                "sequence_length": 411,
                "batch_size": "automatic",
                "gpu_max_mem_percentage": 0.7,
                "sequential_device_map": True,
            },
            "checkpoint_quantization_config": {
                "quant_method": "modelopt",
                "quant_algo": "W4A16_AWQ",
            },
        },
    )

    card = build_trt_card(metadata, "example/trt-model", hf_token=None)

    assert "Scenario License" in card
    assert "scenario-dataset" in card
    assert "automatic" in card
    assert "scenario-revision" in card
