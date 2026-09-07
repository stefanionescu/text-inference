"""Parse checkpoint quantization metadata without runtime dependencies."""

from __future__ import annotations

from typing import cast
from config.model.quantization import (
    MODELOPT_METHOD,
    MODEL_CONFIG_FILENAME,
    MODELOPT_ALGORITHM_FIELD,
    QUANTIZATION_CONFIG_FIELD,
    MODELOPT_ALGORITHM_FORMATS,
    QUANTIZATION_METHOD_FIELDS,
)


def _mapping(value: object) -> dict[str, object]:
    """Return a string-keyed metadata mapping."""
    if not isinstance(value, dict):
        message = "Model configuration must contain a JSON object"
        raise TypeError(message)
    return cast("dict[str, object]", value)


def quantization_metadata(filename: str, payload: object) -> dict[str, object] | None:
    """Extract quantization metadata from one supported configuration payload."""
    config = _mapping(payload)
    if filename == MODEL_CONFIG_FILENAME:
        quantization = config.get(QUANTIZATION_CONFIG_FIELD)
        return None if quantization is None else _mapping(quantization)
    quantization = config.get(QUANTIZATION_CONFIG_FIELD)
    return _mapping(quantization) if quantization is not None else config


def _declared_method(metadata: dict[str, object]) -> str:
    """Read one exact declared quantization method."""
    methods = {value for field in QUANTIZATION_METHOD_FIELDS if isinstance((value := metadata.get(field)), str)}
    if not methods:
        message = "Quantization metadata must declare quant_method or quantization_method"
        raise ValueError(message)
    if len(methods) > 1:
        message = f"Conflicting quantization methods were declared: {sorted(methods)}"
        raise ValueError(message)
    return methods.pop()


def detect_metadata_format(metadata: dict[str, object]) -> str:
    """Return the exact format represented by one metadata object."""
    method = _declared_method(metadata)
    if method != MODELOPT_METHOD:
        return method
    algorithm = metadata.get(MODELOPT_ALGORITHM_FIELD)
    if not isinstance(algorithm, str):
        message = f"Quantization metadata must declare {MODELOPT_ALGORITHM_FIELD}"
        raise TypeError(message)
    detected_format = MODELOPT_ALGORITHM_FORMATS.get(algorithm)
    if detected_format is None:
        message = f"Unsupported ModelOpt quantization algorithm: {algorithm!r}"
        raise ValueError(message)
    return detected_format


def detect_payload_formats(payloads: list[tuple[str, object]]) -> str | None:
    """Return the single quantization format declared across payloads."""
    formats = {
        detect_metadata_format(metadata)
        for filename, payload in payloads
        if (metadata := quantization_metadata(filename, payload)) is not None
    }
    if not formats:
        return None
    if len(formats) > 1:
        message = f"Conflicting quantization formats were declared: {sorted(formats)}"
        raise ValueError(message)
    return formats.pop()


__all__ = ["detect_metadata_format", "detect_payload_formats", "quantization_metadata"]
