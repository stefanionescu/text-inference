"""Persist quantization provenance and cache identity."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, cast
import hashlib
from pathlib import Path
from datetime import UTC, datetime
from tempfile import NamedTemporaryFile
import contextlib
from dataclasses import dataclass

from config.model.quantization import (
    METADATA_FILENAME,
    MODEL_CONFIG_FILENAME,
    METADATA_SCHEMA_VERSION,
    QUANTIZATION_CONFIG_FIELD,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from src.quantization.source import SourceIdentity

_JSON_INDENT = 2
_TIMESTAMP_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def _validate_json_mapping(value: object) -> dict[str, object]:
    """Return one string-keyed JSON object.

    Args:
        value: Value to check or convert.

    Returns:
        One string-keyed JSON object.

    Raises:
        TypeError: Quantization metadata must contain a JSON object.

    """
    if not isinstance(value, dict):
        message = "Quantization metadata must contain a JSON object"
        raise TypeError(message)
    return cast("dict[str, object]", value)


@dataclass(frozen=True, slots=True)
class QuantizationRequest:
    """Inputs that determine one quantized checkpoint.

    Attributes:
        engine: Inference engine that serves the request.
        quantization_format: Format of the quantization.
        source: Source checkpoint to read.
        quantizer: Quantizer settings of the export.
        quantization: Name of the quantization format.
        calibration: Calibration settings of the export.

    """

    engine: str
    quantization_format: str
    source: SourceIdentity
    quantizer: Mapping[str, object]
    quantization: Mapping[str, object]
    calibration: Mapping[str, object]

    def build_cache_payload(self) -> dict[str, object]:
        """Return the deterministic cache-identity payload.

        Returns:
            The deterministic cache-identity payload.

        """
        return {
            "engine": self.engine,
            "format": self.quantization_format,
            "source": self.source.build_metadata(),
            "quantizer": dict(self.quantizer),
            "quantization": dict(self.quantization),
            "calibration": dict(self.calibration),
        }

    @property
    def cache_key(self) -> str:
        """Return the canonical cache key."""
        encoded = json.dumps(
            self.build_cache_payload(),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode()
        return hashlib.sha256(encoded).hexdigest()

    def build_metadata(
        self,
        *,
        exported_quantization: Mapping[str, object],
        environment: Mapping[str, object],
    ) -> dict[str, object]:
        """Return complete checkpoint provenance.

        Args:
            exported_quantization: Exported quantization.
            environment: Environment variables to read.

        Returns:
            Complete checkpoint provenance.

        """
        return {
            "schema_version": METADATA_SCHEMA_VERSION,
            "cache_key": self.cache_key,
            **self.build_cache_payload(),
            "checkpoint_quantization_config": dict(exported_quantization),
            "environment": dict(environment),
            "created_at": datetime.now(UTC).strftime(_TIMESTAMP_FORMAT),
        }


def read_provenance(checkpoint_folder: Path) -> dict[str, object]:
    """Read and validate one provenance document.

    Args:
        checkpoint_folder: Folder of the checkpoint.

    Returns:
        And validate one provenance document.

    Raises:
        ValueError: Unsupported quantization metadata schema.

    """
    payload = json.loads((checkpoint_folder / METADATA_FILENAME).read_text(encoding="utf-8"))
    metadata = _validate_json_mapping(payload)
    if metadata.get("schema_version") != METADATA_SCHEMA_VERSION:
        message = "Unsupported quantization metadata schema"
        raise ValueError(message)
    return metadata


def cache_matches(checkpoint_folder: Path, request: QuantizationRequest) -> bool:
    """Return whether persisted metadata matches the requested export.

    Args:
        checkpoint_folder: Folder of the checkpoint.
        request: Request to run.

    Returns:
        Whether persisted metadata matches the requested export.

    """
    try:
        metadata = read_provenance(checkpoint_folder)
    except (OSError, TypeError, ValueError, json.JSONDecodeError):
        return False
    return metadata.get("cache_key") == request.cache_key


def write_provenance(
    checkpoint_folder: Path,
    request: QuantizationRequest,
    *,
    exported_quantization: Mapping[str, object],
    environment: Mapping[str, object],
) -> None:
    """Atomically persist complete quantization provenance.

    Args:
        checkpoint_folder: Folder of the checkpoint.
        request: Request to run.
        exported_quantization: Exported quantization.
        environment: Environment variables to read.

    """
    checkpoint_folder.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=checkpoint_folder,
            prefix=".quantization_metadata.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            json.dump(
                request.build_metadata(
                    exported_quantization=exported_quantization,
                    environment=environment,
                ),
                temporary,
                ensure_ascii=False,
                indent=_JSON_INDENT,
                sort_keys=True,
            )
            temporary.write("\n")
        destination = temporary_path.with_name(METADATA_FILENAME)
        # The atomic rename stays in the operator-selected checkpoint folder.
        temporary_path.replace(destination)
        temporary_path = None
    finally:
        if temporary_path is not None:
            with contextlib.suppress(OSError):
                temporary_path.unlink()


def require_provenance(
    checkpoint_folder: Path,
    *,
    engine: str,
    expected_format: str,
) -> dict[str, object]:
    """Read provenance and require the expected engine and format.

    Args:
        checkpoint_folder: Folder of the checkpoint.
        engine: Inference engine that serves the request.
        expected_format: Format of the expected.

    Returns:
        Provenance and require the expected engine and format.

    Raises:
        ValueError: Checkpoint provenance does not describe `engine` `expected_format`.

    """
    metadata = read_provenance(checkpoint_folder)
    if metadata.get("engine") != engine or metadata.get("format") != expected_format:
        message = f"Checkpoint provenance does not describe {engine} {expected_format}"
        raise ValueError(message)
    return metadata


def read_export_quantization(checkpoint_folder: Path) -> dict[str, object]:
    """Read the exported checkpoint quantization configuration.

    Args:
        checkpoint_folder: Folder of the checkpoint.

    Returns:
        The exported checkpoint quantization configuration.

    Raises:
        ValueError: Exported checkpoint does not contain quantization_config.

    """
    config = _validate_json_mapping(
        json.loads((checkpoint_folder / MODEL_CONFIG_FILENAME).read_text(encoding="utf-8")),
    )
    quantization = config.get(QUANTIZATION_CONFIG_FIELD)
    if quantization is None:
        message = "Exported checkpoint does not contain quantization_config"
        raise ValueError(message)
    return _validate_json_mapping(quantization)


__all__ = [
    "QuantizationRequest",
    "cache_matches",
    "read_export_quantization",
    "read_provenance",
    "require_provenance",
    "write_provenance",
]
