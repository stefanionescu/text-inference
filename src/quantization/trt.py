"""Choose cache reuse and finalize ModelOpt checkpoints."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING
from pathlib import Path
import argparse
import platform
import importlib.metadata

from config.model.trt import MODELOPT_QUANTIZER_NAME, MODELOPT_CALIBRATION_BATCH_SIZE
from src.quantization.source import derive_source_identity
from config.model.quantization import TRT_ENGINE, INT4_AWQ_FORMAT, BINARY_FLAG_VALUES, QUANTIZATIONS_BY_ENGINE
from src.quantization.checkpoint import CHECKPOINT_VALIDATION_ERRORS, copy_source_assets, validate_checkpoint
from src.quantization.provenance import QuantizationRequest, cache_matches, write_provenance, read_export_quantization
from src.quantization.repository import read_repository_revision

if TYPE_CHECKING:
    from collections.abc import Sequence

_CACHE_REBUILD = "rebuild"
_CACHE_REUSE = "reuse"


def _parse_binary_flag(value: str) -> bool:
    """Parse one binary command value."""
    if value not in BINARY_FLAG_VALUES:
        message = "Binary values must be 0 or 1"
        raise argparse.ArgumentTypeError(message)
    return value == "1"


def _add_request_arguments(parser: argparse.ArgumentParser) -> None:
    """Add shared ModelOpt artifact arguments."""
    parser.add_argument("--source-model", required=True)
    parser.add_argument("--source-dir", required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--checkpoint-dir", required=True)
    parser.add_argument(
        "--format",
        dest="quantization_format",
        required=True,
        choices=QUANTIZATIONS_BY_ENGINE[TRT_ENGINE],
    )
    parser.add_argument("--calibration-dataset", required=True)
    parser.add_argument("--calibration-samples", required=True, type=int)
    parser.add_argument("--calibration-sequence-length", required=True, type=int)
    parser.add_argument("--awq-block-size", required=True, type=int)
    parser.add_argument("--kv-cache-format", required=True)
    parser.add_argument("--gpu-max-mem-percentage", required=True, type=float)
    parser.add_argument("--sequential-device-map", required=True, type=_parse_binary_flag)
    parser.add_argument("--modelopt-repository", required=True)


def _parse_arguments(argument_values: Sequence[str] | None) -> argparse.Namespace:
    """Parse TRT artifact commands."""
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    cache_parser = subparsers.add_parser("cache")
    _add_request_arguments(cache_parser)
    cache_parser.add_argument("--force-rebuild", dest="is_rebuild_forced", action="store_true")

    finalize_parser = subparsers.add_parser("finalize")
    _add_request_arguments(finalize_parser)
    finalize_parser.add_argument("--gpu-name", required=True)
    finalize_parser.add_argument("--sm-arch", required=True)
    finalize_parser.add_argument("--cuda-version", required=True)
    return parser.parse_args(argument_values)


def _build_request(arguments: argparse.Namespace) -> QuantizationRequest:
    """Build the exact ModelOpt cache request."""
    modelopt_repository = Path(arguments.modelopt_repository).resolve(strict=True)
    revision = read_repository_revision(modelopt_repository)
    source = derive_source_identity(
        arguments.source_model,
        Path(arguments.source_dir),
        arguments.source_revision,
    )
    quantization: dict[str, object] = {
        "qformat": arguments.quantization_format,
        "kv_cache_qformat": arguments.kv_cache_format,
    }
    if arguments.quantization_format == INT4_AWQ_FORMAT:
        quantization["awq_block_size"] = arguments.awq_block_size
    return QuantizationRequest(
        engine=TRT_ENGINE,
        quantization_format=arguments.quantization_format,
        source=source,
        quantizer={
            "name": MODELOPT_QUANTIZER_NAME,
            "version": importlib.metadata.version("nvidia-modelopt"),
            "revision": revision,
        },
        quantization=quantization,
        calibration={
            "dataset": arguments.calibration_dataset,
            "num_samples": arguments.calibration_samples,
            "sequence_length": arguments.calibration_sequence_length,
            "batch_size": MODELOPT_CALIBRATION_BATCH_SIZE,
            "gpu_max_mem_percentage": arguments.gpu_max_mem_percentage,
            "sequential_device_map": arguments.sequential_device_map,
        },
    )


def _choose_cache_action(arguments: argparse.Namespace) -> str:
    """Return whether a matching TRT checkpoint can be reused."""
    if arguments.is_rebuild_forced:
        return _CACHE_REBUILD
    checkpoint_dir = Path(arguments.checkpoint_dir).expanduser().resolve()
    request = _build_request(arguments)
    if not cache_matches(checkpoint_dir, request):
        return _CACHE_REBUILD
    try:
        validate_checkpoint(checkpoint_dir, TRT_ENGINE, arguments.quantization_format)
    except CHECKPOINT_VALIDATION_ERRORS:
        return _CACHE_REBUILD
    return _CACHE_REUSE


def _finalize_checkpoint(arguments: argparse.Namespace) -> None:
    """Preserve assets, validate the export, and write provenance."""
    checkpoint_dir = Path(arguments.checkpoint_dir).expanduser().resolve()
    copy_source_assets(Path(arguments.source_dir), checkpoint_dir)
    validate_checkpoint(checkpoint_dir, TRT_ENGINE, arguments.quantization_format)
    write_provenance(
        checkpoint_dir,
        _build_request(arguments),
        exported_quantization=read_export_quantization(checkpoint_dir),
        environment={
            "gpu_name": arguments.gpu_name,
            "sm_arch": arguments.sm_arch,
            "cuda_version": arguments.cuda_version,
            "python_version": platform.python_version(),
        },
    )


def main(argument_values: Sequence[str] | None = None) -> int:
    """Run one TRT cache or finalization command."""
    arguments = _parse_arguments(argument_values)
    if arguments.command == "cache":
        sys.stdout.write(f"{_choose_cache_action(arguments)}\n")
        return 0
    _finalize_checkpoint(arguments)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
