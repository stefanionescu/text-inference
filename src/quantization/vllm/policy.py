"""Select safe compressed-tensors recipes from model configuration."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from config.model.vllm import (
    MOE_SCHEME,
    DENSE_SCHEME,
    MODEL_TYPE_FIELD,
    MOE_MODEL_FAMILY,
    MOE_EXPERT_FIELDS,
    MOE_WNA16_BACKEND,
    DENSE_MODEL_FAMILY,
    MOE_IGNORES_BY_TYPE,
    QWEN_MOE_MODEL_TYPE,
    MODELOPT_FP4_BACKEND,
    QUANTIZATION_TARGETS,
    DENSE_AWQ_DUO_SCALING,
    DENSE_IGNORED_MODULES,
    QUANTIZATION_GROUP_SIZE,
    QUANTIZATION_WEIGHT_BITS,
    MODEL_POSITION_LIMIT_FIELD,
)
from config.model.quantization import GPTQ_FORMAT, NVFP4_FORMAT

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(frozen=True, slots=True)
class QuantizationPolicy:
    """Effective LLM Compressor recipe policy."""

    model_type: str
    model_family: str
    scheme: str
    weight_bits: int
    group_size: int
    is_symmetric: bool
    targets: tuple[str, ...]
    ignored_modules: tuple[str, ...]
    awq_duo_scaling: str | None
    is_all_expert_calibration: bool

    def build_metadata(self) -> dict[str, object]:
        """Return JSON-compatible recipe metadata."""
        return {
            "model_type": self.model_type,
            "model_family": self.model_family,
            "scheme": self.scheme,
            "weight_bits": self.weight_bits,
            "group_size": self.group_size,
            "symmetric": self.is_symmetric,
            "targets": list(self.targets),
            "ignored_modules": list(self.ignored_modules),
            "awq_duo_scaling": self.awq_duo_scaling,
            "moe_calibrate_all_experts": self.is_all_expert_calibration,
        }


def _has_multiple_experts(expert_count: object) -> bool:
    """Return whether a config value declares multiple experts."""
    return isinstance(expert_count, int) and not isinstance(expert_count, bool) and expert_count > 1


def is_moe_config(text_config: Mapping[str, object]) -> bool:
    """Detect MoE architecture from explicit model configuration fields."""
    return any(_has_multiple_experts(text_config.get(field_name)) for field_name in MOE_EXPERT_FIELDS)


def choose_quantization_backend(
    quantization_format: str | None,
    model_config: Mapping[str, object],
) -> str | None:
    """Choose the vLLM backend required by the checkpoint architecture."""
    if quantization_format is None:
        return None
    if quantization_format == NVFP4_FORMAT:
        return MODELOPT_FP4_BACKEND
    model_type = model_config.get(MODEL_TYPE_FIELD)
    if quantization_format == GPTQ_FORMAT and model_type == QWEN_MOE_MODEL_TYPE:
        return MOE_WNA16_BACKEND
    return quantization_format


def validate_sequence_length(text_config: Mapping[str, object], sequence_length: int) -> None:
    """Reject calibration lengths beyond an explicit text-model limit."""
    maximum_positions = text_config.get(MODEL_POSITION_LIMIT_FIELD)
    if isinstance(maximum_positions, int) and sequence_length > maximum_positions:
        message = f"Calibration sequence length {sequence_length} exceeds model limit {maximum_positions}"
        raise ValueError(message)


def select_policy(
    model_config: Mapping[str, object],
    text_config: Mapping[str, object],
) -> QuantizationPolicy:
    """Select a validated dense or architecture-specific MoE policy."""
    model_type = model_config.get(MODEL_TYPE_FIELD)
    if not isinstance(model_type, str) or not model_type:
        message = "Model configuration must declare a model type"
        raise TypeError(message)

    if is_moe_config(text_config):
        ignored_modules = MOE_IGNORES_BY_TYPE.get(model_type)
        if ignored_modules is None:
            message = f"MoE model type {model_type!r} is not supported for local compressed-tensors export"
            raise ValueError(message)
        return QuantizationPolicy(
            model_type=model_type,
            model_family=MOE_MODEL_FAMILY,
            scheme=MOE_SCHEME,
            weight_bits=QUANTIZATION_WEIGHT_BITS,
            group_size=QUANTIZATION_GROUP_SIZE,
            is_symmetric=True,
            targets=QUANTIZATION_TARGETS,
            ignored_modules=ignored_modules,
            awq_duo_scaling=None,
            is_all_expert_calibration=True,
        )
    return QuantizationPolicy(
        model_type=model_type,
        model_family=DENSE_MODEL_FAMILY,
        scheme=DENSE_SCHEME,
        weight_bits=QUANTIZATION_WEIGHT_BITS,
        group_size=QUANTIZATION_GROUP_SIZE,
        is_symmetric=False,
        targets=QUANTIZATION_TARGETS,
        ignored_modules=DENSE_IGNORED_MODULES,
        awq_duo_scaling=DENSE_AWQ_DUO_SCALING,
        is_all_expert_calibration=False,
    )


__all__ = [
    "QuantizationPolicy",
    "choose_quantization_backend",
    "is_moe_config",
    "select_policy",
    "validate_sequence_length",
]
