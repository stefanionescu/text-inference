"""Tests for repository provenance reads."""

import pytest
from pathlib import Path
from src.quantization.repository import read_repository_revision


def _create_repository(tmp_path: Path, head: str) -> tuple[Path, Path]:
    """Create a minimal repository metadata directory."""
    repository = tmp_path / "modelopt"
    git_directory = repository / ".git"
    git_directory.mkdir(parents=True)
    (git_directory / "HEAD").write_text(head, encoding="utf-8")
    return repository, git_directory


def test_detached_git_head(tmp_path: Path) -> None:
    """A detached checkout supplies its revision directly."""
    repository, _git_directory = _create_repository(tmp_path, "A" * 40)

    assert read_repository_revision(repository) == "a" * 40


def test_loose_git_reference(tmp_path: Path) -> None:
    """A branch checkout resolves a loose reference."""
    repository, git_directory = _create_repository(tmp_path, "ref: refs/heads/main")
    reference_path = git_directory / "refs/heads/main"
    reference_path.parent.mkdir(parents=True)
    reference_path.write_text("b" * 40, encoding="utf-8")

    assert read_repository_revision(repository) == "b" * 40


def test_packed_git_reference(tmp_path: Path) -> None:
    """A branch checkout resolves a packed reference when needed."""
    repository, git_directory = _create_repository(tmp_path, "ref: refs/tags/release")
    (git_directory / "packed-refs").write_text(f"{'c' * 40} refs/tags/release\n", encoding="utf-8")

    assert read_repository_revision(repository) == "c" * 40


def test_invalid_git_head(tmp_path: Path) -> None:
    """Malformed revisions cannot enter provenance."""
    repository, _git_directory = _create_repository(tmp_path, "not-a-revision")

    with pytest.raises(RuntimeError, match="Invalid Git revision"):
        read_repository_revision(repository)
