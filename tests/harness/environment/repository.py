"""Repository path discovery for test scripts."""

from __future__ import annotations

import os
from pathlib import Path


def configure_repository_path() -> str:
    """Return the repository root and expose it through YAP_REPO_ROOT.

    Returns:
        The repository root and expose it through YAP_REPO_ROOT.

    """
    repository_root = Path(__file__).resolve().parents[3]
    repository_root_text = str(repository_root)
    os.environ.setdefault("YAP_REPO_ROOT", repository_root_text)
    return repository_root_text


__all__ = ["configure_repository_path"]
