"""Acquire immutable local snapshots for quantization sources."""

from __future__ import annotations

import os
import re
import sys
import hashlib
import argparse
import huggingface_hub
from pathlib import Path
from dataclasses import dataclass
from huggingface_hub import HfApi
from typing import TYPE_CHECKING, cast
from config.model.quantization import (
    HUB_SOURCE_KIND,
    LOCAL_SOURCE_KIND,
    DEFAULT_MODEL_REVISION,
    HUB_COMMIT_PATTERN_TEXT,
    CHECKPOINT_ASSET_FILENAMES,
    SOURCE_FINGERPRINT_SUFFIXES,
)

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


def _is_source_asset(path: Path) -> bool:
    """Return whether a file affects quantization or tokenizer behavior."""
    return path.name in CHECKPOINT_ASSET_FILENAMES or path.suffix in SOURCE_FINGERPRINT_SUFFIXES


def _fingerprint_local_source(model_dir: Path) -> str:
    """Fingerprint relevant files without reading multi-gigabyte weights."""
    digest = hashlib.sha256()
    file_count = 0
    for path in sorted(model_dir.rglob("*")):
        if not path.is_file() or not _is_source_asset(path):
            continue
        file_stat = path.stat()
        relative_path = path.relative_to(model_dir).as_posix()
        digest.update(f"{relative_path}\0{file_stat.st_size}\0{file_stat.st_mtime_ns}\n".encode())
        file_count += 1
    if file_count == 0:
        message = "Local model does not contain checkpoint files"
        raise ValueError(message)
    return f"local:{digest.hexdigest()}"


def _build_local_source(model_dir: Path) -> SourceSnapshot:
    """Build the identity for a local source directory."""
    path = model_dir.resolve(strict=True)
    return SourceSnapshot(
        identity=SourceIdentity(
            kind=LOCAL_SOURCE_KIND,
            model=path.name,
            requested_revision=None,
            resolved_revision=_fingerprint_local_source(path),
        ),
        path=path,
    )


def _acquire_hub_source(
    model: str,
    revision: str,
    *,
    token: str | None,
    cache_dir: str | None,
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
        cache_dir=cache_dir,
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


def acquire_source(
    model: str,
    revision: str,
    *,
    token: str | None,
    cache_dir: str | None,
) -> SourceSnapshot:
    """Acquire a local directory or immutable Hugging Face snapshot."""
    model_path = Path(model).expanduser()
    if model_path.is_dir():
        return _build_local_source(model_path)
    if model_path.exists():
        message = "Model path must be a directory"
        raise NotADirectoryError(message)
    return _acquire_hub_source(model, revision, token=token, cache_dir=cache_dir)


def derive_source_identity(
    model: str,
    source_dir: Path,
    revision: str,
) -> SourceIdentity:
    """Derive source identity from an acquired local path."""
    model_path = Path(model).expanduser()
    if model_path.is_dir():
        return _build_local_source(model_path).identity

    resolved_revision = source_dir.resolve(strict=True).name
    if not _COMMIT_PATTERN.fullmatch(resolved_revision):
        message = "Hugging Face snapshot path does not contain a commit revision"
        raise ValueError(message)
    return SourceIdentity(
        kind=HUB_SOURCE_KIND,
        model=model,
        requested_revision=revision,
        resolved_revision=resolved_revision,
    )


def _parse_arguments(argument_values: Sequence[str] | None) -> argparse.Namespace:
    """Parse source acquisition arguments."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--revision", default=DEFAULT_MODEL_REVISION)
    return parser.parse_args(argument_values)


def main(argument_values: Sequence[str] | None = None) -> int:
    """Acquire one model and print its local snapshot path."""
    arguments = _parse_arguments(argument_values)
    snapshot = acquire_source(
        arguments.model,
        arguments.revision,
        token=os.environ.get("HF_TOKEN"),
        cache_dir=os.environ.get("HUGGINGFACE_HUB_CACHE"),
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
