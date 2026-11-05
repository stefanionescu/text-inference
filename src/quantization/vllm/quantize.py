"""Bind the vLLM quantization workflow to LLM Compressor."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, cast
import platform

import torch
from transformers import AutoConfig, AutoModelForCausalLM
import llmcompressor
from llmcompressor import oneshot
from llmcompressor.utils import load_context
from llmcompressor.modifiers.quantization import QuantizationModifier
from llmcompressor.modifiers.transform.awq import AWQModifier

from src.quantization.vllm.runner import (
    QuantizationSettings,
    run_quantization,
)

if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import Mapping, Sequence

    from src.quantization.source import SourceSnapshot
    from src.quantization.vllm.policy import QuantizationPolicy

_PRIMARY_GPU_INDEX = 0


def _string_key_mapping(value: object) -> dict[str, object]:
    """Return a string-keyed model configuration mapping.

    Args:
        value: Output of a configuration `to_dict` call.

    Returns:
        The same dictionary, typed with string keys.

    Raises:
        TypeError: The value is not a dictionary with string keys.

    """
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        message = "Model configuration must be a string-keyed mapping"
        raise TypeError(message)
    return cast("dict[str, object]", value)


class _LLMCompressorRuntime:
    """Expose concrete LLM Compressor behavior to the portable workflow."""

    @property
    def version(self) -> str:
        """Return the installed LLM Compressor version."""
        return str(llmcompressor.__version__)

    def read_model_configuration(
        self,
        source_path: Path,
    ) -> tuple[Mapping[str, object], Mapping[str, object]]:
        """Load the snapshot configuration through `AutoConfig`, restricted to local files.

        Args:
            source_path: Verified snapshot folder passed to `AutoConfig.from_pretrained`.

        Returns:
            The `to_dict` output of the configuration and of its decoder text configuration.

        """
        # reason: The snapshot path is verified and loading is restricted to local files.
        configuration = AutoConfig.from_pretrained(
            source_path,
            trust_remote_code=True,
            local_files_only=True,
        )
        return (
            _string_key_mapping(configuration.to_dict()),
            _string_key_mapping(configuration.get_text_config(decoder=True).to_dict()),
        )

    def quantize(
        self,
        source: SourceSnapshot,
        checkpoint_folder: Path,
        policy: QuantizationPolicy,
        settings: QuantizationSettings,
    ) -> None:
        """Create a compressed-tensors checkpoint with LLM Compressor.

        Args:
            source: Snapshot whose model and processor load from local files.
            checkpoint_folder: Output folder that `oneshot` writes to.
            policy: Policy that supplies the AWQ modifier, scheme, targets, and ignored modules.
            settings: Dataset and calibration sizes passed to `oneshot`.

        """
        with load_context(AutoModelForCausalLM):
            # reason: The snapshot path is verified and loading is restricted to local files.
            model = AutoModelForCausalLM.from_pretrained(
                source.path,
                dtype=torch.bfloat16,
                trust_remote_code=True,
                device_map=None,
                local_files_only=True,
            )
        awq_modifier = (
            AWQModifier(duo_scaling=policy.awq_duo_scaling) if policy.awq_duo_scaling is not None else AWQModifier()
        )
        oneshot(
            model=model,
            processor=str(source.path),
            trust_remote_code_model=True,
            dataset=settings.dataset,
            recipe=[
                awq_modifier,
                QuantizationModifier(
                    scheme=policy.scheme,
                    targets=list(policy.targets),
                    ignore=list(policy.ignored_modules),
                ),
            ],
            output_dir=str(checkpoint_folder),
            max_seq_length=settings.sequence_length,
            num_calibration_samples=settings.samples,
            batch_size=settings.batch_size,
            pipeline=settings.pipeline,
            moe_calibrate_all_experts=policy.is_all_expert_calibration,
        )

    def environment_metadata(self, environment: Mapping[str, str]) -> Mapping[str, object]:
        """Collect execution provenance that does not constrain cache reuse.

        Args:
            environment: Variables that can supply `GPU_SM_ARCH`.

        Returns:
            GPU name, SM architecture, CUDA version, and Python version.

        """
        gpu_name = torch.cuda.get_device_name(_PRIMARY_GPU_INDEX) if torch.cuda.is_available() else "unavailable"
        return {
            "gpu_name": gpu_name,
            "sm_arch": environment.get("GPU_SM_ARCH", "unknown"),
            "cuda_version": torch.version.cuda or "unavailable",
            "python_version": platform.python_version(),
        }


def main(argument_values: Sequence[str] | None = None) -> int:
    """Quantize one model through the pinned LLM Compressor public API.

    Args:
        argument_values: Arguments with the model and output folder; None reads `sys.argv`.

    Returns:
        The exit code from `run_quantization`.

    """
    return run_quantization(argument_values, environment=os.environ, compressor=_LLMCompressorRuntime())


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
