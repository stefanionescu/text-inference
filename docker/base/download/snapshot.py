"""Download one immutable Hugging Face snapshot during an image build."""

from __future__ import annotations

import os
import re
import sys
from typing import TYPE_CHECKING, cast
from pathlib import Path

import huggingface_hub

if TYPE_CHECKING:
    from collections.abc import Callable

_DOWNLOAD_SNAPSHOT: Callable[..., str] = cast("Callable[..., str]", huggingface_hub.snapshot_download)


def main() -> int:
    """Download the exact checkpoint declared by Docker build arguments.

    Returns:
        The resulting number.

    """
    model = os.environ["MODEL"]
    revision = os.environ["MODEL_REVISION"]
    target = os.environ["MODEL_PATH"]
    if re.fullmatch(r"[0-9a-fA-F]{40}", revision) is None:
        sys.stderr.write("MODEL_REVISION must be a 40-character Hugging Face commit SHA\n")
        return 1

    secret_path = Path("/run/secrets/hf_token")
    token = secret_path.read_text(encoding="utf-8").strip() if secret_path.is_file() else None
    _DOWNLOAD_SNAPSHOT(
        repo_id=model,
        revision=revision,
        local_dir=target,
        token=token,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = ["main"]
