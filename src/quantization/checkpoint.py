"""Preserve and validate portable quantized checkpoints."""

from __future__ import annotations

import shutil
from typing import TYPE_CHECKING, cast
from pathlib import Path
import argparse

from transformers import AutoTokenizer

from src.tokens.validation import validate_tokenizer_exists
from config.model.quantization import (
    MODEL_CONFIG_FILENAME,
    QUANTIZATIONS_BY_ENGINE,
    CHECKPOINT_ASSET_FILENAMES,
)
from src.quantization.detection import detect_format, validate_engine

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

CHECKPOINT_VALIDATION_ERRORS = (ImportError, KeyError, OSError, RuntimeError, TypeError, ValueError)
_CREATE_TOKENIZER: Callable[..., object] = cast("Callable[..., object]", AutoTokenizer.from_pretrained)


def copy_source_assets(source_dir: Path, checkpoint_dir: Path) -> None:
    """Copy tokenizer, processor, template, and custom-code assets."""
    source_root = source_dir.resolve(strict=True)
    checkpoint_root = checkpoint_dir.resolve(strict=True)
    if source_root == checkpoint_root:
        return

    for filename in CHECKPOINT_ASSET_FILENAMES:
        source_file = source_root / filename
        if source_file.is_file():
            shutil.copy2(source_file, checkpoint_root / filename)

    for source_file in sorted(source_root.glob("*.py")):
        shutil.copy2(source_file, checkpoint_root / source_file.name)


def validate_tokenizer_assets(checkpoint_dir: Path) -> None:
    """Require a locally loadable tokenizer."""
    validation = validate_tokenizer_exists(str(checkpoint_dir))
    if not validation.is_valid:
        message = validation.error_message or "Checkpoint tokenizer validation failed"
        raise ValueError(message)
    _CREATE_TOKENIZER(
        checkpoint_dir,
        trust_remote_code=True,
        local_files_only=True,
    )


def validate_checkpoint(checkpoint_dir: Path, engine: str, expected_format: str) -> Path:
    """Validate weights, tokenizer, and exact quantization metadata."""
    validate_engine(engine)
    if expected_format not in QUANTIZATIONS_BY_ENGINE[engine]:
        message = f"Quantization format {expected_format!r} is not supported by {engine}"
        raise ValueError(message)

    checkpoint_root = checkpoint_dir.resolve(strict=True)
    if not (checkpoint_root / MODEL_CONFIG_FILENAME).is_file():
        message = "Checkpoint config.json is missing"
        raise FileNotFoundError(message)
    if not any(checkpoint_root.glob("*.safetensors")):
        message = "Checkpoint does not contain safetensors weights"
        raise FileNotFoundError(message)
    validate_tokenizer_assets(checkpoint_root)
    detected_format = detect_format(str(checkpoint_root), engine)
    if detected_format != expected_format:
        message = f"Checkpoint declares {detected_format!r}, expected {expected_format!r}"
        raise ValueError(message)
    return checkpoint_root


def _parse_arguments(argument_values: Sequence[str] | None) -> argparse.Namespace:
    """Parse checkpoint-validation arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--checkpoint-dir", required=True)
    parser.add_argument("--engine", required=True, choices=QUANTIZATIONS_BY_ENGINE)
    parser.add_argument("--format", dest="quantization_format", required=True)
    return parser.parse_args(argument_values)


def main(argument_values: Sequence[str] | None = None) -> int:
    """Validate one checkpoint."""
    arguments = _parse_arguments(argument_values)
    validate_checkpoint(Path(arguments.checkpoint_dir), arguments.engine, arguments.quantization_format)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "CHECKPOINT_VALIDATION_ERRORS",
    "copy_source_assets",
    "main",
    "validate_checkpoint",
    "validate_tokenizer_assets",
]
