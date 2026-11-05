"""Resolve unchanged, exported, and online quantization requests."""

from __future__ import annotations

from dataclasses import dataclass

from config.model.quantization import (
    FP8_FORMAT,
    TRT_ENGINE,
    VLLM_ENGINE,
    QUANTIZATIONS_BY_ENGINE,
    COMPRESSED_TENSORS_FORMAT,
)

UNCHANGED_ACTION = "unchanged"
EXPORT_ACTION = "export"
ONLINE_ACTION = "online"


@dataclass(frozen=True, slots=True)
class QuantizationPlan:
    """Resolved checkpoint action and eventual runtime format."""

    action: str
    source_format: str | None
    requested_format: str | None
    runtime_format: str | None


def validate_engine(engine: str) -> None:
    """Require one supported inference engine."""
    if engine not in QUANTIZATIONS_BY_ENGINE:
        message = f"Inference engine must be one of {tuple(QUANTIZATIONS_BY_ENGINE)}, got {engine!r}"
        raise ValueError(message)


def _validate_requested_format(engine: str, requested_format: str | None) -> None:
    """Require a requested export format supported by the selected engine."""
    if requested_format is None:
        return
    if requested_format not in QUANTIZATIONS_BY_ENGINE[engine]:
        allowed = "|".join(QUANTIZATIONS_BY_ENGINE[engine])
        message = f"Quantization format {requested_format!r} is incompatible with {engine}; expected {allowed}"
        raise ValueError(message)


def _validate_existing_format(engine: str, source_format: str | None) -> None:
    """Require an existing format compatible with the selected engine."""
    if source_format is None or source_format in QUANTIZATIONS_BY_ENGINE[engine]:
        return
    message = f"Checkpoint format {source_format!r} is incompatible with the {engine} engine"
    raise ValueError(message)


def build_quantization_plan(
    engine: str,
    source_format: str | None,
    requested_format: str | None,
) -> QuantizationPlan:
    """Resolve the complete source/requested-format matrix."""
    validate_engine(engine)
    _validate_requested_format(engine, requested_format)
    if source_format is not None and requested_format is not None:
        message = (
            f"Checkpoint already declares {source_format}. "
            "Omit `--quantization` to deploy it unchanged; re-quantization is not supported."
        )
        raise ValueError(message)
    _validate_existing_format(engine, source_format)
    if requested_format is None:
        return QuantizationPlan(UNCHANGED_ACTION, source_format, None, source_format)
    if engine == VLLM_ENGINE and requested_format == FP8_FORMAT:
        return QuantizationPlan(ONLINE_ACTION, None, requested_format, requested_format)
    exportable = engine == TRT_ENGINE or requested_format == COMPRESSED_TENSORS_FORMAT
    if not exportable:
        message = f"{requested_format} requires an existing compatible checkpoint for {engine}"
        raise ValueError(message)
    return QuantizationPlan(EXPORT_ACTION, None, requested_format, requested_format)


__all__ = [
    "EXPORT_ACTION",
    "ONLINE_ACTION",
    "UNCHANGED_ACTION",
    "QuantizationPlan",
    "build_quantization_plan",
    "validate_engine",
]
