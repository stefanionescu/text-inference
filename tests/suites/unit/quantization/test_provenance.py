"""Unit tests for quantized-checkpoint cache provenance."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.quantization.source import SourceIdentity
from src.quantization.provenance import QuantizationRequest, cache_matches, write_provenance

if TYPE_CHECKING:
    from pathlib import Path


def _build_request(source_revision: str) -> QuantizationRequest:
    """Build one scenario request."""
    return QuantizationRequest(
        engine="vllm",
        quantization_format="compressed-tensors",
        source=SourceIdentity(
            kind="hub",
            model="example/base-model",
            requested_revision="main",
            resolved_revision=source_revision,
        ),
        quantizer={"name": "compressor", "version": "scenario-version"},
        quantization={"scheme": "scenario-scheme"},
        calibration={"dataset": "scenario-dataset", "num_samples": 17},
    )


def test_matching_cache_reused(tmp_path: Path) -> None:
    """Test identical source and policy metadata enables reuse."""
    request = _build_request("a" * 40)
    write_provenance(
        tmp_path,
        request,
        exported_quantization={"quant_method": "compressed-tensors"},
        environment={"gpu_name": "scenario-gpu"},
    )

    assert cache_matches(tmp_path, request)


def test_source_change_invalidates(tmp_path: Path) -> None:
    """Test an upstream source update invalidates cached weights."""
    original = _build_request("a" * 40)
    updated = _build_request("b" * 40)
    write_provenance(
        tmp_path,
        original,
        exported_quantization={"quant_method": "compressed-tensors"},
        environment={"gpu_name": "scenario-gpu"},
    )

    assert not cache_matches(tmp_path, updated)
