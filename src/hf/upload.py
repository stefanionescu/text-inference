"""Command-line and Hub steps both checkpoint-upload commands run identically."""

from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path
import argparse

from huggingface_hub import HfApi

from config.model.publishing import HF_MODEL_REPO_TYPE, HF_DEFAULT_REVISION, MODEL_CARD_FILENAME

if TYPE_CHECKING:
    from collections.abc import Sequence


def parse_upload_arguments(
    argument_values: Sequence[str] | None,
    description: str | None,
    *,
    is_format_required: bool,
) -> argparse.Namespace:
    """Parse the stable upload flags; only the TensorRT command also requires --format.

    Args:
        argument_values: Command-line arguments to parse.
        description: Description.
        is_format_required: Whether format is required.

    Returns:
        The stable upload flags; only the TensorRT command also requires --format.

    """
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("--checkpoint-dir", dest="checkpoint_folder", required=True)
    parser.add_argument("--repo-id", required=True)
    if is_format_required:
        parser.add_argument("--format", dest="quantization_format", required=True)
    parser.add_argument("--private", action="store_true")
    return parser.parse_args(argument_values)


def require_checkpoint_folder(checkpoint_folder: str) -> Path:
    """Resolve the flag value to an existing path, rejecting anything but a directory.

    Args:
        checkpoint_folder: Folder of the checkpoint.

    Returns:
        The flag value to an existing path, rejecting anything but a directory.

    Raises:
        NotADirectoryError: Checkpoint must be a directory.

    """
    resolved_folder = Path(checkpoint_folder).resolve(strict=True)
    if not resolved_folder.is_dir():
        message = "Checkpoint must be a directory"
        raise NotADirectoryError(message)
    return resolved_folder


def publish_checkpoint(
    checkpoint_folder: Path,
    model_card: str,
    arguments: argparse.Namespace,
    hf_token: str,
    commit_message: str,
    ignore_patterns: Sequence[str],
) -> None:
    """Write the card into the checkpoint, then create the Hub repository and upload the folder.

    Args:
        checkpoint_folder: Folder of the checkpoint.
        model_card: Model card.
        arguments: Parsed command-line arguments.
        hf_token: Hugging Face token.
        commit_message: Commit message.
        ignore_patterns: Ignore patterns.

    """
    (checkpoint_folder / MODEL_CARD_FILENAME).write_text(model_card, encoding="utf-8")

    hf_client = HfApi(token=hf_token)
    hf_client.create_repo(
        repo_id=arguments.repo_id,
        exist_ok=True,
        repo_type=HF_MODEL_REPO_TYPE,
        private=arguments.private,
    )
    hf_client.upload_folder(
        folder_path=checkpoint_folder,
        repo_id=arguments.repo_id,
        repo_type=HF_MODEL_REPO_TYPE,
        revision=HF_DEFAULT_REVISION,
        commit_message=commit_message,
        ignore_patterns=list(ignore_patterns),
    )


__all__ = ["parse_upload_arguments", "publish_checkpoint", "require_checkpoint_folder"]
