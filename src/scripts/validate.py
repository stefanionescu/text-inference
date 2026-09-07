"""Early model validation before startup."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from config.model.allowlists import (
    ALLOWED_TRT_MOE_MODELS,
    ALLOWED_TRT_BASE_MODELS,
    ALLOWED_VLLM_MOE_MODELS,
    ALLOWED_VLLM_BASE_MODELS,
    ALLOWED_TRT_QUANTIZED_MODELS,
    ALLOWED_VLLM_QUANTIZED_MODELS,
)
from config.model.quantization import (
    TRT_ENGINE,
    QUANTIZATIONS_BY_ENGINE,
)


def validate_models(
    model: str | None,
    engine: str,
    quantization: str | None,
) -> list[str]:
    """Validate model configuration against allowlists."""
    errors: list[str] = []

    if engine not in QUANTIZATIONS_BY_ENGINE:
        errors.append(f"INFERENCE_ENGINE must be one of {tuple(QUANTIZATIONS_BY_ENGINE)}, got: {engine}")
        return errors

    if engine == TRT_ENGINE:
        allowed_models = ALLOWED_TRT_BASE_MODELS + ALLOWED_TRT_MOE_MODELS + ALLOWED_TRT_QUANTIZED_MODELS
    else:
        allowed_models = ALLOWED_VLLM_BASE_MODELS + ALLOWED_VLLM_MOE_MODELS + ALLOWED_VLLM_QUANTIZED_MODELS
    allowed_quantizations = QUANTIZATIONS_BY_ENGINE[engine]
    if not model:
        errors.append("MODEL is required")
    else:
        allowlisted = Path(model).exists() or model in allowed_models
        if not allowlisted:
            errors.append(f"MODEL must be allowlisted for engine '{engine}' or a local path: {model}")

    if quantization is not None and quantization not in allowed_quantizations:
        errors.append(
            f"RUNTIME_QUANTIZATION must be one of {'|'.join(allowed_quantizations)} for {engine}, got: {quantization}",
        )

    return errors


if __name__ == "__main__":
    model = os.environ.get("MODEL") or None
    engine = os.environ.get("INFERENCE_ENGINE") or ""
    quantization = os.environ.get("RUNTIME_QUANTIZATION") or None

    errors = validate_models(
        model=model,
        engine=engine,
        quantization=quantization,
    )

    if errors:
        for error in errors:
            sys.stderr.write(str(f"[validate] ✗ {error}") + "\n")
        sys.exit(1)

    sys.stdout.write("[validate] ✓ Model validation passed" + "\n")
    sys.exit(0)
