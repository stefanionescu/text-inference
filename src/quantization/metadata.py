"""Parse checkpoint metadata and fingerprint local sources without runtime dependencies."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
import hashlib

from config.model.quantization import (
    MODELOPT_METHOD,
    MODEL_CONFIG_FILENAME,
    MODELOPT_ALGORITHM_FIELD,
    QUANTIZATION_CONFIG_FIELD,
    CHECKPOINT_ASSET_FILENAMES,
    MODELOPT_ALGORITHM_FORMATS,
    QUANTIZATION_METHOD_FIELDS,
    SOURCE_FINGERPRINT_SUFFIXES,
)

if TYPE_CHECKING:
    from pathlib import Path


def _mapping(value: object) -> dict[str, object]:
    """Return a string-keyed metadata mapping.

    Args:
        value: Value to check or convert.

    Returns:
        A string-keyed metadata mapping.

    Raises:
        TypeError: Model configuration must contain a JSON object.

    """
    if not isinstance(value, dict):
        message = "Model configuration must contain a JSON object"
        raise TypeError(message)
    return cast("dict[str, object]", value)


def _declared_method(metadata: dict[str, object]) -> str:
    """Read one exact declared quantization method.

    Args:
        metadata: Metadata fields to read.

    Returns:
        One exact declared quantization method.

    Raises:
        ValueError: Quantization metadata must declare quant_method or quantization_method.

    """
    methods = {value for field in QUANTIZATION_METHOD_FIELDS if isinstance((value := metadata.get(field)), str)}
    if not methods:
        message = "Quantization metadata must declare quant_method or quantization_method"
        raise ValueError(message)
    if len(methods) > 1:
        message = f"Conflicting quantization methods were declared: {sorted(methods)}"
        raise ValueError(message)
    return methods.pop()


def quantization_metadata(filename: str, payload: object) -> dict[str, object] | None:
    """Extract quantization metadata from one supported configuration payload.

    Args:
        filename: Name of the file.
        payload: Decoded message fields.

    Returns:
        Quantization metadata from one supported configuration payload.

    """
    config = _mapping(payload)
    if filename == MODEL_CONFIG_FILENAME:
        quantization = config.get(QUANTIZATION_CONFIG_FIELD)
        return None if quantization is None else _mapping(quantization)
    quantization = config.get(QUANTIZATION_CONFIG_FIELD)
    return _mapping(quantization) if quantization is not None else config


def detect_metadata_format(metadata: dict[str, object]) -> str:
    """Return the exact format represented by one metadata object.

    Args:
        metadata: Metadata fields to read.

    Returns:
        The exact format represented by one metadata object.

    Raises:
        TypeError: Quantization metadata must declare `MODELOPT_ALGORITHM_FIELD`.
        ValueError: Unsupported ModelOpt quantization algorithm: `algorithm`.

    """
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
    """Return the single quantization format declared across payloads.

    Args:
        payloads: Decoded messages.

    Returns:
        The single quantization format declared across payloads.

    Raises:
        ValueError: Conflicting quantization formats were declared: `sorted`.

    """
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


def fingerprint_local_source(model_folder: Path) -> str:
    """Hash the names, sizes, and mtimes of checkpoint files, never reading multi-gigabyte weights.

    Args:
        model_folder: Folder of the model.

    Returns:
        The resulting text.

    Raises:
        ValueError: Local model does not contain checkpoint files.

    """
    digest = hashlib.sha256()
    file_count = 0
    for path in sorted(model_folder.rglob("*")):
        if not path.is_file():
            continue
        if path.name not in CHECKPOINT_ASSET_FILENAMES and path.suffix not in SOURCE_FINGERPRINT_SUFFIXES:
            continue
        file_stat = path.stat()
        relative_path = path.relative_to(model_folder).as_posix()
        digest.update(f"{relative_path}\0{file_stat.st_size}\0{file_stat.st_mtime_ns}\n".encode())
        file_count += 1
    if file_count == 0:
        message = "Local model does not contain checkpoint files"
        raise ValueError(message)
    return f"local:{digest.hexdigest()}"


__all__ = [
    "detect_metadata_format",
    "detect_payload_formats",
    "fingerprint_local_source",
    "quantization_metadata",
]
