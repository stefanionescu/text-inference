"""Generate and upload rich ModelOpt checkpoints for TensorRT-LLM."""

from __future__ import annotations

import os
import sys
import json
from typing import TYPE_CHECKING
from pathlib import Path
import argparse

from huggingface_hub import HfApi

from config.model.trt import TRT_VERSION
from src.hf.model_card import (
    format_model_card,
    read_metadata_text,
    read_metadata_section,
    build_provenance_fields,
)
from config.model.publishing import (
    TRT_FORMAT_LABELS,
    HF_MODEL_REPO_TYPE,
    TRT_UPLOAD_MESSAGE,
    HF_DEFAULT_REVISION,
    MODEL_CARD_FILENAME,
    NOT_APPLICABLE_LABEL,
    TRT_GPU_REQUIREMENTS,
    TRT_WEIGHT_PRECISIONS,
    MODEL_CARD_JSON_INDENT,
    PYTHON_RUNTIME_VERSION,
    TRT_HF_IGNORE_PATTERNS,
    TRT_MODEL_CARD_TEMPLATE,
)
from config.model.quantization import TRT_ENGINE
from src.quantization.checkpoint import validate_checkpoint
from src.quantization.provenance import require_provenance

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def build_model_card(
    metadata: Mapping[str, object],
    repo_id: str,
    *,
    hf_token: str | None,
) -> str:
    """Build the detailed checkpoint-only TensorRT model card."""
    card_fields = build_provenance_fields(metadata, repo_id, hf_token=hf_token)
    quantization = read_metadata_section(metadata, "quantization")
    calibration = read_metadata_section(metadata, "calibration")
    quantizer = read_metadata_section(metadata, "quantizer")
    environment = read_metadata_section(metadata, "environment")
    checkpoint_quantization = read_metadata_section(metadata, "checkpoint_quantization_config")
    quantization_format = read_metadata_text(metadata, "format")
    card_fields.update(
        {
            "quantization_format": quantization_format,
            "quantization_label": TRT_FORMAT_LABELS[quantization_format],
            "weight_precision": TRT_WEIGHT_PRECISIONS[quantization_format],
            "kv_cache_format": quantization.get("kv_cache_qformat"),
            "awq_block_size": quantization.get("awq_block_size", NOT_APPLICABLE_LABEL),
            "modelopt_version": read_metadata_text(quantizer, "version"),
            "modelopt_revision": read_metadata_text(quantizer, "revision"),
            "tensorrt_llm_version": TRT_VERSION,
            "calibration_dataset": read_metadata_text(calibration, "dataset"),
            "calibration_samples": calibration.get("num_samples"),
            "calibration_sequence_length": calibration.get("sequence_length"),
            "calibration_batch_size": calibration.get("batch_size"),
            "gpu_memory_fraction": calibration.get("gpu_max_mem_percentage"),
            "sequential_device_map": calibration.get("sequential_device_map"),
            "gpu_name": environment.get("gpu_name", "unknown"),
            "sm_arch": environment.get("sm_arch", "unknown"),
            "cuda_version": environment.get("cuda_version", "unknown"),
            "python_version": environment.get("python_version", "unknown"),
            "python_requirement": PYTHON_RUNTIME_VERSION,
            "gpu_requirement": TRT_GPU_REQUIREMENTS[quantization_format],
            "quantization_summary": json.dumps(
                {
                    "request": {
                        "quantization": quantization,
                        "calibration": calibration,
                    },
                    "checkpoint_quantization_config": checkpoint_quantization,
                },
                indent=MODEL_CARD_JSON_INDENT,
                sort_keys=True,
            ),
        },
    )
    return format_model_card(TRT_MODEL_CARD_TEMPLATE, card_fields)


def _parse_arguments(argument_values: Sequence[str] | None) -> argparse.Namespace:
    """Parse the stable checkpoint-upload command."""
    parser = argparse.ArgumentParser(description="Push a TensorRT-LLM ModelOpt checkpoint")
    parser.add_argument("--checkpoint-dir", dest="checkpoint_folder", required=True)
    parser.add_argument("--repo-id", required=True)
    parser.add_argument("--format", dest="quantization_format", required=True)
    parser.add_argument("--private", action="store_true")
    return parser.parse_args(argument_values)


def main(argument_values: Sequence[str] | None = None) -> int:
    """Generate a model card and upload one ModelOpt checkpoint."""
    arguments = _parse_arguments(argument_values)
    checkpoint_folder = Path(arguments.checkpoint_folder).resolve(strict=True)
    if not checkpoint_folder.is_dir():
        message = "Checkpoint must be a directory"
        raise NotADirectoryError(message)
    validate_checkpoint(checkpoint_folder, TRT_ENGINE, arguments.quantization_format)
    metadata = require_provenance(
        checkpoint_folder,
        engine=TRT_ENGINE,
        expected_format=arguments.quantization_format,
    )
    hf_token = os.environ["HF_TOKEN"]
    model_card = build_model_card(metadata, arguments.repo_id, hf_token=hf_token)
    (checkpoint_folder / MODEL_CARD_FILENAME).write_text(model_card, encoding="utf-8")

    hf_client = HfApi(token=hf_token)
    hf_client.create_repo(
        repo_id=arguments.repo_id,
        exist_ok=True,
        repo_type=HF_MODEL_REPO_TYPE,
        private=arguments.private,
    )
    hf_client.upload_folder(
        folder_path=checkpoint_folder,
        repo_id=arguments.repo_id,
        repo_type=HF_MODEL_REPO_TYPE,
        revision=HF_DEFAULT_REVISION,
        commit_message=TRT_UPLOAD_MESSAGE.format(quantization_format=arguments.quantization_format),
        ignore_patterns=list(TRT_HF_IGNORE_PATTERNS),
    )
    sys.stdout.write(f"[trt-hf] Upload complete: {arguments.repo_id}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_model_card", "main"]
