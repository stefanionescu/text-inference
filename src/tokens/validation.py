"""Tokenizer and local model-directory validation."""

from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass


@dataclass(slots=True)
class TokenizerValidationResult:
    """Result of tokenizer validation."""

    is_valid: bool
    error_message: str | None
    model_path: str
    has_tokenizer_json: bool
    has_tokenizer_config: bool


def _missing_tokenizer_message(model_path: str, tokenizer_json: str, tokenizer_config: str) -> str:
    """Build the missing-tokenizer validation message."""
    return (
        f"Tokenizer files not found in model directory: {model_path}\n"
        "Expected at least one of:\n"
        f"  - {tokenizer_json}\n"
        f"  - {tokenizer_config}\n"
        "\n"
        "If using a pre-quantized model from HuggingFace:\n"
        "  Ensure the download completed successfully and includes tokenizer files.\n"
        "\n"
        "If using a locally quantized model:\n"
        "  Re-run quantization to regenerate the tokenizer files."
    )


def require_local_model_directory(model_path: str | Path) -> Path:
    """Return an existing resolved local model directory."""
    if not str(model_path):
        message = "Model path is empty"
        raise ValueError(message)
    candidate = Path(model_path).expanduser()
    try:
        resolved = candidate.resolve(strict=True)
    except FileNotFoundError as exception:
        message = f"Model directory does not exist: {candidate}"
        raise FileNotFoundError(message) from exception
    if not resolved.is_dir():
        message = f"Model path must be a directory: {resolved}"
        raise NotADirectoryError(message)
    return resolved


def validate_tokenizer_exists(model_path: str) -> TokenizerValidationResult:
    """Validate that a tokenizer exists locally for the given model.

    Args:
        model_path: Local model directory path.

    Returns:
        TokenizerValidationResult with validation status and fragments.

    """
    result: TokenizerValidationResult
    try:
        model_root = require_local_model_directory(model_path)
    except (OSError, ValueError) as error:
        result = TokenizerValidationResult(
            is_valid=False,
            error_message=str(error),
            model_path=model_path,
            has_tokenizer_json=False,
            has_tokenizer_config=False,
        )
    else:
        tokenizer_json = model_root / "tokenizer.json"
        tokenizer_config = model_root / "tokenizer_config.json"

        has_tokenizer_json = tokenizer_json.is_file()
        has_tokenizer_config = tokenizer_config.is_file()

        if has_tokenizer_json or has_tokenizer_config:
            result = TokenizerValidationResult(
                is_valid=True,
                error_message=None,
                model_path=model_path,
                has_tokenizer_json=has_tokenizer_json,
                has_tokenizer_config=has_tokenizer_config,
            )
        else:
            result = TokenizerValidationResult(
                is_valid=False,
                error_message=_missing_tokenizer_message(model_path, str(tokenizer_json), str(tokenizer_config)),
                model_path=model_path,
                has_tokenizer_json=False,
                has_tokenizer_config=False,
            )

    return result


__all__ = [
    "TokenizerValidationResult",
    "require_local_model_directory",
    "validate_tokenizer_exists",
]
