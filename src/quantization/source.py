"""Acquire immutable local snapshots for quantization sources."""

from __future__ import annotations

import os
import re
import sys
from typing import TYPE_CHECKING, cast
from pathlib import Path
import argparse
from dataclasses import dataclass

import huggingface_hub
from huggingface_hub import HfApi

from config.model.quantization import (
    HUB_SOURCE_KIND,
    LOCAL_SOURCE_KIND,
    DEFAULT_MODEL_REVISION,
    HUB_COMMIT_PATTERN_TEXT,
)
from src.quantization.metadata import fingerprint_local_source

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

_COMMIT_PATTERN = re.compile(HUB_COMMIT_PATTERN_TEXT)
_DOWNLOAD_SNAPSHOT: Callable[..., str] = cast("Callable[..., str]", huggingface_hub.snapshot_download)


@dataclass(frozen=True, slots=True)
class SourceIdentity:
    """Stable identity for one quantization source."""

    kind: str
    model: str
    requested_revision: str | None
    resolved_revision: str

    def build_metadata(self) -> dict[str, object]:
        """Return JSON-compatible source metadata."""
        return {
            "kind": self.kind,
            "model": self.model,
            "requested_revision": self.requested_revision,
            "resolved_revision": self.resolved_revision,
        }


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    """Acquired source identity and local checkpoint path."""

    identity: SourceIdentity
    path: Path


def _build_local_source(model_folder: Path) -> SourceSnapshot:
    """Build the identity for a local source directory."""
    path = model_folder.resolve(strict=True)
    return SourceSnapshot(
        identity=SourceIdentity(
            kind=LOCAL_SOURCE_KIND,
            model=path.name,
            requested_revision=None,
            resolved_revision=fingerprint_local_source(path),
        ),
        path=path,
    )


def _acquire_hub_source(
    model: str,
    revision: str,
    *,
    token: str | None,
    cache_folder: str | None,
) -> SourceSnapshot:
    """Acquire one immutable Hugging Face snapshot."""
    resolved_revision = HfApi(token=token).model_info(repo_id=model, revision=revision).sha
    if not isinstance(resolved_revision, str) or not _COMMIT_PATTERN.fullmatch(resolved_revision):
        message = "Hugging Face did not return an immutable model revision"
        raise ValueError(message)
    snapshot_path = _DOWNLOAD_SNAPSHOT(
        repo_id=model,
        revision=resolved_revision,
        token=token,
        cache_dir=cache_folder,
    )
    return SourceSnapshot(
        identity=SourceIdentity(
            kind=HUB_SOURCE_KIND,
            model=model,
            requested_revision=revision,
            resolved_revision=resolved_revision,
        ),
        path=Path(snapshot_path).resolve(strict=True),
    )


def _parse_arguments(argument_values: Sequence[str] | None) -> argparse.Namespace:
    """Parse source acquisition arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", default=DEFAULT_MODEL_REVISION)
    return parser.parse_args(argument_values)


def acquire_source(
    model: str,
    revision: str,
    *,
    token: str | None,
    cache_folder: str | None,
) -> SourceSnapshot:
    """Acquire a local directory or immutable Hugging Face snapshot."""
    model_path = Path(model).expanduser()
    if model_path.is_dir():
        return _build_local_source(model_path)
    if model_path.exists():
        message = "Model path must be a directory"
        raise NotADirectoryError(message)
    return _acquire_hub_source(model, revision, token=token, cache_folder=cache_folder)


def derive_source_identity(
    model: str,
    source_folder: Path,
    revision: str,
) -> SourceIdentity:
    """Derive source identity from an acquired local path."""
    model_path = Path(model).expanduser()
    if model_path.is_dir():
        return _build_local_source(model_path).identity

    resolved_revision = source_folder.resolve(strict=True).name
    if not _COMMIT_PATTERN.fullmatch(resolved_revision):
        message = "Hugging Face snapshot path does not contain a commit revision"
        raise ValueError(message)
    return SourceIdentity(
        kind=HUB_SOURCE_KIND,
        model=model,
        requested_revision=revision,
        resolved_revision=resolved_revision,
    )


def main(argument_values: Sequence[str] | None = None) -> int:
    """Acquire one model and print its local snapshot path."""
    arguments = _parse_arguments(argument_values)
    snapshot = acquire_source(
        arguments.model,
        arguments.revision,
        token=os.environ.get("HF_TOKEN"),
        cache_folder=os.environ.get("HUGGINGFACE_HUB_CACHE"),
    )
    sys.stdout.write(f"{snapshot.path}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = [
    "SourceIdentity",
    "SourceSnapshot",
    "acquire_source",
    "derive_source_identity",
    "main",
]
