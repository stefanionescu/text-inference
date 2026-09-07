"""Unit tests for deployment quantization decisions."""

from __future__ import annotations

import json
import pytest
from typing import TYPE_CHECKING
from src.quantization.inspection import inspect_model
from src.quantization.policy import (
    EXPORT_ACTION,
    ONLINE_ACTION,
    UNCHANGED_ACTION,
    build_quantization_plan,
)
from config.model.quantization import (
    AWQ_FORMAT,
    FP8_FORMAT,
    TRT_ENGINE,
    GPTQ_FORMAT,
    VLLM_ENGINE,
    INT4_AWQ_FORMAT,
    COMPRESSED_TENSORS_FORMAT,
)

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("engine", "source_format", "requested_format", "expected_action", "runtime_format"),
    [
        (TRT_ENGINE, None, None, UNCHANGED_ACTION, None),
        (VLLM_ENGINE, None, None, UNCHANGED_ACTION, None),
        (TRT_ENGINE, FP8_FORMAT, None, UNCHANGED_ACTION, FP8_FORMAT),
        (VLLM_ENGINE, AWQ_FORMAT, None, UNCHANGED_ACTION, AWQ_FORMAT),
        (TRT_ENGINE, None, INT4_AWQ_FORMAT, EXPORT_ACTION, INT4_AWQ_FORMAT),
        (VLLM_ENGINE, None, COMPRESSED_TENSORS_FORMAT, EXPORT_ACTION, COMPRESSED_TENSORS_FORMAT),
        (VLLM_ENGINE, None, FP8_FORMAT, ONLINE_ACTION, FP8_FORMAT),
    ],
)
def test_quantization_matrix(
    engine: str,
    source_format: str | None,
    requested_format: str | None,
    expected_action: str,
    runtime_format: str | None,
) -> None:
    """Test unchanged, exported, and online deployment decisions."""
    plan = build_quantization_plan(engine, source_format, requested_format)

    assert plan.action == expected_action
    assert plan.source_format == source_format
    assert plan.requested_format == requested_format
    assert plan.runtime_format == runtime_format


def test_requantization_rejected() -> None:
    """Test any requested conversion of a quantized source is rejected."""
    with pytest.raises(ValueError, match="re-quantization is not supported") as error:
        build_quantization_plan(VLLM_ENGINE, GPTQ_FORMAT, FP8_FORMAT)

    message = str(error.value)
    assert GPTQ_FORMAT in message
    assert "Omit `--quantization` to deploy it unchanged; re-quantization is not supported." in message


def test_existing_format_compatibility() -> None:
    """Test an existing checkpoint is never converted for another engine."""
    with pytest.raises(ValueError, match="incompatible with the trt engine"):
        build_quantization_plan(TRT_ENGINE, AWQ_FORMAT, None)


def test_unexportable_request_rejected() -> None:
    """Test requests without a repository export path fail precisely."""
    with pytest.raises(ValueError, match="requires an existing compatible checkpoint"):
        build_quantization_plan(VLLM_ENGINE, None, GPTQ_FORMAT)


def test_local_inspection_identity(tmp_path: Path) -> None:
    """Test local inspection separates source identity and runtime format."""
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    config = {"quantization_config": {"quant_method": AWQ_FORMAT}}
    (model_dir / "config.json").write_text(json.dumps(config), encoding="utf-8")

    inspection = inspect_model(str(model_dir), VLLM_ENGINE, None)

    assert inspection.resolved_revision.startswith("local:")
    assert inspection.detected_format == AWQ_FORMAT
    assert inspection.plan.action == UNCHANGED_ACTION
