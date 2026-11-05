"""Run the portable vLLM quantization workflow."""

from __future__ import annotations

import sys
import shutil
from typing import TYPE_CHECKING, Protocol
from pathlib import Path
import argparse
from dataclasses import dataclass

from config.model.vllm import (
    LLM_COMPRESSOR_NAME,
    CALIBRATION_PIPELINES,
    DEFAULT_CALIBRATION_DATASET,
    DEFAULT_CALIBRATION_SAMPLES,
    DEFAULT_CALIBRATION_PIPELINE,
    DEFAULT_CALIBRATION_BATCH_SIZE,
    DEFAULT_CALIBRATION_SEQUENCE_LENGTH,
)
from src.quantization.source import SourceSnapshot, acquire_source
from config.model.quantization import (
    VLLM_ENGINE,
    BINARY_FLAG_VALUES,
    DEFAULT_MODEL_REVISION,
    COMPRESSED_TENSORS_FORMAT,
)
from src.quantization.detection import detect_local_format
from src.quantization.checkpoint import (
    CHECKPOINT_VALIDATION_ERRORS,
    copy_source_assets,
    validate_checkpoint,
    validate_tokenizer_assets,
)
from src.quantization.provenance import (
    QuantizationRequest,
    cache_matches,
    write_provenance,
    read_export_quantization,
)
from src.quantization.vllm.policy import QuantizationPolicy, select_policy, validate_sequence_length

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence


class CompressorRuntime(Protocol):
    """LLM Compressor behavior required by the portable workflow."""

    @property
    def version(self) -> str:
        """Return the LLM Compressor package version.

        Raises:
            NotImplementedError: This stub always raises; `_LLMCompressorRuntime` supplies the version.

        """
        raise NotImplementedError

    def read_model_configuration(
        self,
        source_path: Path,
    ) -> tuple[Mapping[str, object], Mapping[str, object]]:
        """Read model and decoder configuration from a local snapshot.

        Args:
            source_path: Folder of the acquired source snapshot.

        Returns:
            The model configuration and the decoder configuration, as string-keyed mappings.

        Raises:
            NotImplementedError: This stub always raises; `_LLMCompressorRuntime` reads the configuration.

        """
        raise NotImplementedError(source_path)

    def quantize(
        self,
        source: SourceSnapshot,
        checkpoint_folder: Path,
        policy: QuantizationPolicy,
        settings: QuantizationSettings,
        /,
    ) -> None:
        """Create a compressed-tensors checkpoint.

        Args:
            source: Acquired source snapshot to quantize.
            checkpoint_folder: Empty folder that receives the export.
            policy: Policy chosen for this model.
            settings: Calibration settings read from the environment.

        Raises:
            NotImplementedError: This stub always raises; `_LLMCompressorRuntime` runs the quantization.

        """
        raise NotImplementedError(source, checkpoint_folder, policy, settings)

    def environment_metadata(self, environment: Mapping[str, str]) -> Mapping[str, object]:
        """Return execution metadata that does not constrain cache reuse.

        Args:
            environment: Variables that the integration can read.

        Returns:
            Values for the provenance file that cache matching ignores.

        Raises:
            NotImplementedError: This stub always raises; `_LLMCompressorRuntime` collects the metadata.

        """
        raise NotImplementedError(environment)


def _read_positive_integer(environment: Mapping[str, str], key: str, default: int) -> int:
    """Read one positive environment integer.

    Args:
        environment: Variables to read.
        key: Variable name.
        default: Value used when the variable is unset.

    Returns:
        The parsed integer.

    Raises:
        ValueError: `key` must be a positive integer.

    """
    value = int(environment.get(key, str(default)))
    if value < 1:
        message = f"{key} must be a positive integer"
        raise ValueError(message)
    return value


def _read_binary_flag(environment: Mapping[str, str], key: str) -> bool:
    """Read one binary environment flag.

    Args:
        environment: Variables to read.
        key: Variable name; an unset variable reads as off.

    Returns:
        True for `1`, False for `0`.

    Raises:
        ValueError: `key` must be 0 or 1.

    """
    value = environment.get(key, "0")
    if value not in BINARY_FLAG_VALUES:
        message = f"{key} must be 0 or 1"
        raise ValueError(message)
    return value == "1"


@dataclass(frozen=True, slots=True)
class QuantizationSettings:
    """Validated vLLM quantization settings.

    Attributes:
        dataset: Name of the calibration dataset.
        samples: Number of calibration samples.
        sequence_length: Calibration sequence length.
        batch_size: Calibration batch size.
        pipeline: Name of the calibration pipeline.
        source_revision: Source model revision to acquire.
        is_rebuild_forced: Whether the run rebuilds even when a cached checkpoint matches.

    """

    dataset: str
    samples: int
    sequence_length: int
    batch_size: int
    pipeline: str
    source_revision: str
    is_rebuild_forced: bool

    @classmethod
    def read_environment(cls, environment: Mapping[str, str]) -> QuantizationSettings:
        """Build settings from the host environment.

        Args:
            environment: Variables that configure calibration and the source revision.

        Returns:
            Validated settings.

        Raises:
            ValueError: The dataset or revision is empty, or the pipeline is not in `CALIBRATION_PIPELINES`.

        """
        dataset = environment.get("VLLM_CALIBRATION_DATASET", DEFAULT_CALIBRATION_DATASET).strip()
        revision = environment.get("SOURCE_REVISION", DEFAULT_MODEL_REVISION).strip()
        pipeline = environment.get("VLLM_CALIBRATION_PIPELINE", DEFAULT_CALIBRATION_PIPELINE).strip()
        if not dataset or not revision:
            message = "Calibration dataset and model revision must not be empty"
            raise ValueError(message)
        if pipeline not in CALIBRATION_PIPELINES:
            message = f"VLLM_CALIBRATION_PIPELINE must be one of {CALIBRATION_PIPELINES}"
            raise ValueError(message)
        return cls(
            dataset=dataset,
            samples=_read_positive_integer(environment, "VLLM_CALIBRATION_SAMPLES", DEFAULT_CALIBRATION_SAMPLES),
            sequence_length=_read_positive_integer(
                environment,
                "VLLM_CALIBRATION_SEQUENCE_LENGTH",
                DEFAULT_CALIBRATION_SEQUENCE_LENGTH,
            ),
            batch_size=_read_positive_integer(
                environment,
                "VLLM_CALIBRATION_BATCH_SIZE",
                DEFAULT_CALIBRATION_BATCH_SIZE,
            ),
            pipeline=pipeline,
            source_revision=revision,
            is_rebuild_forced=_read_binary_flag(environment, "QUANT_FORCE_REBUILD"),
        )


def _parse_arguments(argument_values: Sequence[str] | None) -> argparse.Namespace:
    """Parse the quantizer command contract.

    Args:
        argument_values: Arguments with the model and output folder; None reads `sys.argv`.

    Returns:
        Namespace with the model and the checkpoint folder.

    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--out", dest="checkpoint_folder", required=True)
    return parser.parse_args(argument_values)


def _build_request(
    source: SourceSnapshot,
    policy: QuantizationPolicy,
    settings: QuantizationSettings,
    compressor_version: str,
) -> QuantizationRequest:
    """Build the complete cache-identity request.

    Args:
        source: Snapshot whose identity enters the request.
        policy: Policy whose metadata enters the request.
        settings: Settings whose calibration values enter the request.
        compressor_version: Quantizer version recorded in the request.

    Returns:
        The complete cache-identity request.

    """
    return QuantizationRequest(
        engine=VLLM_ENGINE,
        quantization_format=COMPRESSED_TENSORS_FORMAT,
        source=source.identity,
        quantizer={
            "name": LLM_COMPRESSOR_NAME,
            "version": compressor_version,
        },
        quantization=policy.build_metadata(),
        calibration={
            "dataset": settings.dataset,
            "num_samples": settings.samples,
            "sequence_length": settings.sequence_length,
            "batch_size": settings.batch_size,
            "pipeline": settings.pipeline,
            "moe_calibrate_all_experts": policy.is_all_expert_calibration,
        },
    )


def _is_cache_usable(checkpoint_folder: Path, request: QuantizationRequest) -> bool:
    """Return whether a matching cache remains a valid checkpoint.

    Args:
        checkpoint_folder: Folder that can hold a cached checkpoint.
        request: Cache identity that the stored provenance must match.

    Returns:
        Whether a matching cache remains a valid checkpoint.

    """
    if not cache_matches(checkpoint_folder, request):
        return False
    try:
        validate_checkpoint(checkpoint_folder, VLLM_ENGINE, COMPRESSED_TENSORS_FORMAT)
    except CHECKPOINT_VALIDATION_ERRORS:
        return False
    return True


def run_quantization(
    argument_values: Sequence[str] | None,
    *,
    environment: Mapping[str, str],
    compressor: CompressorRuntime,
) -> int:
    """Quantize one model through a supplied compressor integration.

    Args:
        argument_values: Arguments with the model and output folder.
        environment: Variables that configure this run.
        compressor: Integration that performs the quantization.

    Returns:
        Exit code 0 after a reused cache or a finished export.

    Raises:
        ValueError: The source checkpoint is already quantized.

    """
    arguments = _parse_arguments(argument_values)
    settings = QuantizationSettings.read_environment(environment)
    checkpoint_folder = Path(arguments.checkpoint_folder).expanduser().resolve()
    source = acquire_source(
        arguments.model,
        settings.source_revision,
        token=environment.get("HF_TOKEN"),
        cache_folder=environment.get("HUGGINGFACE_HUB_CACHE"),
    )
    validate_tokenizer_assets(source.path)
    if detect_local_format(source.path) is not None:
        message = "LLM Compressor requires an unquantized source checkpoint"
        raise ValueError(message)

    model_config, text_config = compressor.read_model_configuration(source.path)
    validate_sequence_length(text_config, settings.sequence_length)
    policy = select_policy(model_config, text_config)
    request = _build_request(source, policy, settings, compressor.version)

    if not settings.is_rebuild_forced and _is_cache_usable(checkpoint_folder, request):
        sys.stdout.write(f"[quant] Reusing compressed-tensors checkpoint: {checkpoint_folder}\n")
        return 0

    if checkpoint_folder.exists():
        shutil.rmtree(checkpoint_folder)
    checkpoint_folder.mkdir(parents=True)
    compressor.quantize(source, checkpoint_folder, policy, settings)
    copy_source_assets(source.path, checkpoint_folder)
    validate_checkpoint(checkpoint_folder, VLLM_ENGINE, COMPRESSED_TENSORS_FORMAT)
    write_provenance(
        checkpoint_folder,
        request,
        exported_quantization=read_export_quantization(checkpoint_folder),
        environment=compressor.environment_metadata(environment),
    )
    sys.stdout.write("[quant] LLM Compressor compressed-tensors export complete\n")
    return 0


__all__ = ["CompressorRuntime", "QuantizationSettings", "run_quantization"]
