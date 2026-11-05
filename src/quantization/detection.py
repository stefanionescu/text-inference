"""Detect exact quantization metadata from checkpoint configuration files."""

from __future__ import annotations

import sys
import json
from typing import TYPE_CHECKING
from pathlib import Path
import argparse

from src.quantization.policy import validate_engine
from config.model.quantization import DEFAULT_MODEL_REVISION, QUANTIZATION_CONFIG_FILENAMES
from src.quantization.metadata import detect_payload_formats
from src.quantization.inspection import inspect_metadata

if TYPE_CHECKING:
    from collections.abc import Sequence


def _parse_arguments(argument_values: Sequence[str] | None) -> argparse.Namespace:
    """Parse internal local-checkpoint detection arguments.

    Args:
        argument_values: Command-line arguments to parse.

    Returns:
        Internal local-checkpoint detection arguments.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("checkpoint")
    return parser.parse_args(argument_values)


def detect_format(
    model: str,
    engine: str,
    *,
    revision: str = DEFAULT_MODEL_REVISION,
    hf_token: str | None = None,
) -> str | None:
    """Read exact quantization metadata and ensure the engine accepts it.

    Args:
        model: Model name or local checkpoint path.
        engine: Inference engine that serves the request.
        revision: Model revision to use.
        hf_token: Hugging Face token.

    Returns:
        Exact quantization metadata and ensure the engine accepts it.

    """
    validate_engine(engine)
    _pinned_revision, detected_format = inspect_metadata(model, revision=revision, token=hf_token)
    return detected_format


def detect_local_format(model_folder: Path) -> str | None:
    """Read quantization metadata from an already acquired local checkpoint.

    Args:
        model_folder: Folder of the model.

    Returns:
        Quantization metadata from an already acquired local checkpoint.

    Raises:
        FileNotFoundError: Model configuration was not found.

    """
    payloads = [
        (filename, json.loads(path.read_text(encoding="utf-8")))
        for filename in QUANTIZATION_CONFIG_FILENAMES
        if (path := model_folder / filename).is_file()
    ]
    if not payloads:
        message = "Model configuration was not found"
        raise FileNotFoundError(message)
    return detect_payload_formats(payloads)


def main(argument_values: Sequence[str] | None = None) -> int:
    """Print the detected format, or an empty line for an unquantized source.

    Args:
        argument_values: Command-line arguments to parse.

    Returns:
        The resulting number.

    """
    arguments = _parse_arguments(argument_values)
    detected_format = detect_local_format(Path(arguments.checkpoint).resolve(strict=True))
    sys.stdout.write(f"{detected_format or ''}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["detect_format", "detect_local_format", "main", "validate_engine"]
