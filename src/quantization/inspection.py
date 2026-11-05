"""Inspect checkpoint identity and metadata before deployment mutation."""

from __future__ import annotations

import os
import sys
import json
from typing import TYPE_CHECKING
from pathlib import Path
import argparse
from dataclasses import dataclass

from config.model.allowlists import (
    ALLOWED_TRT_MOE_MODELS,
    ALLOWED_TRT_BASE_MODELS,
    ALLOWED_VLLM_MOE_MODELS,
    ALLOWED_VLLM_BASE_MODELS,
    ALLOWED_TRT_QUANTIZED_MODELS,
    ALLOWED_VLLM_QUANTIZED_MODELS,
)
from src.quantization.policy import QuantizationPlan, build_quantization_plan
from config.model.quantization import (
    TRT_ENGINE,
    DEFAULT_MODEL_REVISION,
    QUANTIZATION_CONFIG_FILENAMES,
)
from src.quantization.metadata import detect_payload_formats, fingerprint_local_source
from src.quantization.hub_metadata import read_remote_metadata

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


@dataclass(frozen=True, slots=True)
class ModelInspection:
    """Immutable source identity and deployment quantization decision.

    Attributes:
        model: Model name or local checkpoint path.
        resolved_revision: Revision of the resolved.
        detected_format: Format of the detected.
        plan: Prepared plan to carry out.

    """

    model: str
    resolved_revision: str
    detected_format: str | None
    plan: QuantizationPlan


def _local_payloads(model_folder: Path) -> list[tuple[str, object]]:
    """Read supported local quantization configuration files.

    Args:
        model_folder: Folder of the model.

    Returns:
        Supported local quantization configuration files.

    Raises:
        FileNotFoundError: Model configuration was not found.

    """
    payloads = [
        (filename, json.loads(config_path.read_text(encoding="utf-8")))
        for filename in QUANTIZATION_CONFIG_FILENAMES
        if (config_path := model_folder / filename).is_file()
    ]
    if not payloads:
        message = "Model configuration was not found"
        raise FileNotFoundError(message)
    return payloads


def _validate_allowlist(model: str, engine: str) -> None:
    """Require a local directory or an engine-allowlisted Hub model.

    Args:
        model: Model name or local checkpoint path.
        engine: Inference engine that serves the request.

    Raises:
        ValueError: Model must be allowlisted for `engine` or a local directory: `model`.

    """
    if Path(model).is_dir():
        return
    allowed_models = (
        ALLOWED_TRT_BASE_MODELS + ALLOWED_TRT_MOE_MODELS + ALLOWED_TRT_QUANTIZED_MODELS
        if engine == TRT_ENGINE
        else ALLOWED_VLLM_BASE_MODELS + ALLOWED_VLLM_MOE_MODELS + ALLOWED_VLLM_QUANTIZED_MODELS
    )
    if model not in allowed_models:
        message = f"Model must be allowlisted for {engine} or a local directory: {model}"
        raise ValueError(message)


def _parse_arguments(argument_values: Sequence[str] | None) -> argparse.Namespace:
    """Parse the internal early-inspection command.

    Args:
        argument_values: Command-line arguments to parse.

    Returns:
        The internal early-inspection command.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--engine", required=True, choices=("trt", "vllm"))
    parser.add_argument("--quantization")
    parser.add_argument("--revision", default=DEFAULT_MODEL_REVISION)
    return parser.parse_args(argument_values)


def inspect_model(
    model: str,
    engine: str,
    requested_format: str | None,
    *,
    revision: str = DEFAULT_MODEL_REVISION,
    token: str | None = None,
) -> ModelInspection:
    """Resolve source identity, detect metadata, and validate the requested action.

    Args:
        model: Model name or local checkpoint path.
        engine: Inference engine that serves the request.
        requested_format: Format of the requested.
        revision: Model revision to use.
        token: Hugging Face access token or token text.

    Returns:
        Source identity, detect metadata, and validate the requested action.

    """
    _validate_allowlist(model, engine)
    resolved_revision, detected_format = inspect_metadata(model, revision=revision, token=token)
    plan = build_quantization_plan(engine, detected_format, requested_format)
    return ModelInspection(model, resolved_revision, detected_format, plan)


def inspect_metadata(
    model: str,
    *,
    revision: str = DEFAULT_MODEL_REVISION,
    token: str | None = None,
) -> tuple[str, str | None]:
    """Resolve source identity and format without applying engine policy.

    Args:
        model: Model name or local checkpoint path.
        revision: Model revision to use.
        token: Hugging Face access token or token text.

    Returns:
        Source identity and format without applying engine policy.

    Raises:
        NotADirectoryError: Model path must be a directory.

    """
    model_path = Path(model).expanduser()
    if model_path.exists() and not model_path.is_dir():
        message = "Model path must be a directory"
        raise NotADirectoryError(message)
    if model_path.is_dir():
        resolved_revision = fingerprint_local_source(model_path.resolve(strict=True))
        payloads = _local_payloads(model_path)
    else:
        resolved_revision, payloads = read_remote_metadata(model, revision, token)
    detected_format = detect_payload_formats(payloads)
    return resolved_revision, detected_format


def main(argument_values: Sequence[str] | None = None) -> int:
    """Print fixed-key tab-separated inspection results for host orchestration.

    Args:
        argument_values: Command-line arguments to parse.

    Returns:
        The resulting number.

    Raises:
        ValueError: Inspection value for `key` is not safe to persist.

    """
    arguments = _parse_arguments(argument_values)
    try:
        inspection = inspect_model(
            arguments.model,
            arguments.engine,
            arguments.quantization,
            revision=arguments.revision,
            token=os.environ.get("HF_TOKEN"),
        )
    except (OSError, RuntimeError, TypeError, ValueError) as exception:
        sys.stderr.write(f"[inspect] {exception}\n")
        return 1
    values: Mapping[str, str] = {
        "SOURCE_MODEL": inspection.model,
        "SOURCE_REVISION": inspection.resolved_revision,
        "RUNTIME_QUANTIZATION": inspection.plan.runtime_format or "",
        "REQUESTED_QUANTIZATION": inspection.plan.requested_format or "",
        "CHECKPOINT_ACTION": inspection.plan.action,
    }
    for key, value in values.items():
        if any(separator in value for separator in ("\t", "\n", "\r")):
            message = f"Inspection value for {key} is not safe to persist"
            raise ValueError(message)
        sys.stdout.write(f"{key}\t{value}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["ModelInspection", "inspect_metadata", "inspect_model", "main"]
