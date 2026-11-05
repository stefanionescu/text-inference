"""Generate and upload rich vLLM compressed-tensors checkpoints."""

from __future__ import annotations

import os
import sys
import json
from typing import TYPE_CHECKING

from src.hf.upload import publish_checkpoint, parse_upload_arguments, require_checkpoint_folder
from config.model.vllm import VLLM_VERSION
from src.hf.model_card import (
    format_model_card,
    read_metadata_text,
    format_metadata_items,
    read_metadata_section,
    build_provenance_fields,
)
from config.model.publishing import (
    ENABLED_LABEL,
    DISABLED_LABEL,
    ALL_EXPERTS_LABEL,
    VLLM_UPLOAD_MESSAGE,
    NOT_APPLICABLE_LABEL,
    MODEL_CARD_JSON_INDENT,
    VLLM_HF_IGNORE_PATTERNS,
    VLLM_MODEL_CARD_TEMPLATE,
)
from config.model.quantization import VLLM_ENGINE, COMPRESSED_TENSORS_FORMAT
from src.quantization.checkpoint import validate_checkpoint
from src.quantization.provenance import require_provenance

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


def build_model_card(metadata: Mapping[str, object], repo_id: str, *, hf_token: str | None) -> str:
    """Build the detailed compressed-tensors model card.

    Args:
        metadata: Metadata fields to read.
        repo_id: ID of the repo.
        hf_token: Hugging Face token.

    Returns:
        The detailed compressed-tensors model card.

    """
    card_fields = build_provenance_fields(metadata, repo_id, hf_token=hf_token)
    recipe = read_metadata_section(metadata, "quantization")
    calibration = read_metadata_section(metadata, "calibration")
    checkpoint_quantization = read_metadata_section(metadata, "checkpoint_quantization_config")
    quantizer = read_metadata_section(metadata, "quantizer")
    is_symmetric = recipe.get("symmetric") is True
    card_fields.update(
        {
            "quantizer_version": read_metadata_text(quantizer, "version"),
            "quantization_scheme": read_metadata_text(recipe, "scheme"),
            "weight_bits": recipe.get("weight_bits"),
            "group_size": recipe.get("group_size"),
            "zero_point": DISABLED_LABEL if is_symmetric else ENABLED_LABEL,
            "targets": format_metadata_items(recipe.get("targets")),
            "ignored_modules": format_metadata_items(recipe.get("ignored_modules")),
            "model_family": read_metadata_text(recipe, "model_family"),
            "calibration_dataset": read_metadata_text(calibration, "dataset"),
            "calibration_samples": calibration.get("num_samples"),
            "calibration_sequence_length": calibration.get("sequence_length"),
            "calibration_batch_size": calibration.get("batch_size"),
            "calibration_pipeline": read_metadata_text(calibration, "pipeline"),
            "expert_calibration": (
                ALL_EXPERTS_LABEL if calibration.get("moe_calibrate_all_experts") is True else NOT_APPLICABLE_LABEL
            ),
            "vllm_version": VLLM_VERSION,
            "quantization_summary": json.dumps(
                {
                    "recipe": recipe,
                    "checkpoint_quantization_config": checkpoint_quantization,
                },
                indent=MODEL_CARD_JSON_INDENT,
                sort_keys=True,
            ),
        },
    )
    return format_model_card(VLLM_MODEL_CARD_TEMPLATE, card_fields)


def main(argument_values: Sequence[str] | None = None) -> int:
    """Upload the configured checkpoint.

    Args:
        argument_values: Command-line arguments to parse.

    Returns:
        The resulting number.

    """
    arguments = parse_upload_arguments(argument_values, __doc__, is_format_required=False)
    checkpoint_folder = require_checkpoint_folder(arguments.checkpoint_folder)
    validate_checkpoint(checkpoint_folder, VLLM_ENGINE, COMPRESSED_TENSORS_FORMAT)
    metadata = require_provenance(
        checkpoint_folder,
        engine=VLLM_ENGINE,
        expected_format=COMPRESSED_TENSORS_FORMAT,
    )
    hf_token = os.environ["HF_TOKEN"]
    model_card = build_model_card(metadata, arguments.repo_id, hf_token=hf_token)
    publish_checkpoint(checkpoint_folder, model_card, arguments, hf_token, VLLM_UPLOAD_MESSAGE, VLLM_HF_IGNORE_PATTERNS)
    sys.stdout.write(f"[vllm-hf] Upload complete: {arguments.repo_id}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["build_model_card", "main"]
