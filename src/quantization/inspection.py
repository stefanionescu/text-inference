"""Inspect checkpoint identity and metadata before deployment mutation."""

from __future__ import annotations

import os
import re
import sys
from http import HTTPStatus
import json
from typing import TYPE_CHECKING, cast
import hashlib
from pathlib import Path
import argparse
from dataclasses import dataclass
from http.client import HTTPSConnection
from urllib.parse import quote

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
    HUB_COMMIT_PATTERN_TEXT,
    CHECKPOINT_ASSET_FILENAMES,
    SOURCE_FINGERPRINT_SUFFIXES,
    QUANTIZATION_CONFIG_FILENAMES,
)
from src.quantization.metadata import detect_payload_formats

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

_COMMIT_PATTERN = re.compile(HUB_COMMIT_PATTERN_TEXT)
_HUB_HOST = "huggingface.co"
_REQUEST_TIMEOUT_SECONDS = 30.0


@dataclass(frozen=True, slots=True)
class ModelInspection:
    """Immutable source identity and deployment quantization decision."""

    model: str
    resolved_revision: str
    detected_format: str | None
    plan: QuantizationPlan


def _json_request(
    path: str,
    token: str | None,
    *,
    is_missing_allowed: bool = False,
) -> object | None:
    """Read one authenticated Hugging Face JSON response."""
    if not path.startswith("/"):
        message = "Hugging Face request paths must be absolute"
        raise ValueError(message)
    headers = {"Accept": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    connection = HTTPSConnection(_HUB_HOST, timeout=_REQUEST_TIMEOUT_SECONDS)
    try:
        connection.request("GET", path, headers=headers)
        response = connection.getresponse()
        if response.status == HTTPStatus.NOT_FOUND and is_missing_allowed:
            return None
        if not HTTPStatus.OK <= response.status < HTTPStatus.MULTIPLE_CHOICES:
            message = f"Hugging Face request failed with HTTP {response.status}: {path}"
            raise RuntimeError(message)
        return json.loads(response.read())
    finally:
        connection.close()


def _mapping(value: object) -> dict[str, object]:
    """Return one string-keyed JSON mapping."""
    if not isinstance(value, dict):
        message = "Hugging Face returned an invalid model response"
        raise TypeError(message)
    return cast("dict[str, object]", value)


def _local_fingerprint(model_dir: Path) -> str:
    """Fingerprint checkpoint-relevant local files without hashing weights."""
    digest = hashlib.sha256()
    file_count = 0
    for path in sorted(model_dir.rglob("*")):
        if not path.is_file():
            continue
        if path.name not in CHECKPOINT_ASSET_FILENAMES and path.suffix not in SOURCE_FINGERPRINT_SUFFIXES:
            continue
        file_stat = path.stat()
        relative_path = path.relative_to(model_dir).as_posix()
        digest.update(f"{relative_path}\0{file_stat.st_size}\0{file_stat.st_mtime_ns}\n".encode())
        file_count += 1
    if file_count == 0:
        message = "Local model does not contain checkpoint files"
        raise ValueError(message)
    return f"local:{digest.hexdigest()}"


def _local_payloads(model_dir: Path) -> list[tuple[str, object]]:
    """Read supported local quantization configuration files."""
    payloads = [
        (filename, json.loads(config_path.read_text(encoding="utf-8")))
        for filename in QUANTIZATION_CONFIG_FILENAMES
        if (config_path := model_dir / filename).is_file()
    ]
    if not payloads:
        message = "Model configuration was not found"
        raise FileNotFoundError(message)
    return payloads


def _resolved_revision(response: dict[str, object]) -> str:
    """Read and validate one immutable Hub revision."""
    resolved_revision = response.get("sha")
    if not isinstance(resolved_revision, str) or not _COMMIT_PATTERN.fullmatch(resolved_revision):
        message = "Hugging Face did not return an immutable model revision"
        raise ValueError(message)
    return resolved_revision


def _sibling_filenames(response: dict[str, object]) -> set[str]:
    """Read the model repository filenames advertised by the Hub API."""
    siblings = response.get("siblings")
    if not isinstance(siblings, list):
        return set()
    filenames: set[str] = set()
    for sibling_value in cast("list[object]", siblings):
        if isinstance(sibling_value, dict):
            filename = cast("dict[str, object]", sibling_value).get("rfilename")
            if isinstance(filename, str):
                filenames.add(filename)
    return filenames


def _remote_payloads(
    model_path: str,
    resolved_revision: str,
    filenames: set[str],
    token: str | None,
) -> list[tuple[str, object]]:
    """Read the remote checkpoint files that may declare quantization."""
    payloads: list[tuple[str, object]] = []
    for filename in QUANTIZATION_CONFIG_FILENAMES:
        if filenames and filename not in filenames:
            continue
        file_path = f"/{model_path}/resolve/{resolved_revision}/{quote(filename, safe='')}"
        payload = _json_request(file_path, token, is_missing_allowed=True)
        if payload is not None:
            payloads.append((filename, payload))
    if not payloads:
        message = "Model configuration was not found"
        raise FileNotFoundError(message)
    return payloads


def _remote_metadata(model: str, revision: str, token: str | None) -> tuple[str, list[tuple[str, object]]]:
    """Resolve one immutable Hub revision and read its small config files."""
    model_path = quote(model, safe="/")
    revision_path = quote(revision, safe="")
    metadata_path = f"/api/models/{model_path}/revision/{revision_path}"
    response = _mapping(_json_request(metadata_path, token))
    resolved_revision = _resolved_revision(response)
    return resolved_revision, _remote_payloads(
        model_path,
        resolved_revision,
        _sibling_filenames(response),
        token,
    )


def _validate_allowlist(model: str, engine: str) -> None:
    """Require a local directory or an engine-allowlisted Hub model."""
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


def inspect_model(
    model: str,
    engine: str,
    requested_format: str | None,
    *,
    revision: str = DEFAULT_MODEL_REVISION,
    token: str | None = None,
) -> ModelInspection:
    """Resolve source identity, detect metadata, and validate the requested action."""
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
    """Resolve source identity and format without applying engine policy."""
    model_path = Path(model).expanduser()
    if model_path.exists() and not model_path.is_dir():
        message = "Model path must be a directory"
        raise NotADirectoryError(message)
    if model_path.is_dir():
        resolved_revision = _local_fingerprint(model_path.resolve(strict=True))
        payloads = _local_payloads(model_path)
    else:
        resolved_revision, payloads = _remote_metadata(model, revision, token)
    detected_format = detect_payload_formats(payloads)
    return resolved_revision, detected_format


def _parse_arguments(argument_values: Sequence[str] | None) -> argparse.Namespace:
    """Parse the internal early-inspection command."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--engine", required=True, choices=("trt", "vllm"))
    parser.add_argument("--quantization")
    parser.add_argument("--revision", default=DEFAULT_MODEL_REVISION)
    return parser.parse_args(argument_values)


def main(argument_values: Sequence[str] | None = None) -> int:
    """Print fixed-key tab-separated inspection results for host orchestration."""
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
