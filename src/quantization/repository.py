"""Read repository provenance without starting external processes."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

_SHA1_HEX_LENGTH = 40


def _read_git_directory(repository: Path) -> Path:
    """Resolve ordinary clones and Git worktree metadata links."""
    git_metadata = repository / ".git"
    if git_metadata.is_dir():
        return git_metadata.resolve(strict=True)
    git_directory_line = git_metadata.read_text(encoding="utf-8").strip()
    if not git_directory_line.startswith("gitdir: "):
        message = f"Invalid Git metadata file: {git_metadata}"
        raise RuntimeError(message)
    return (repository / git_directory_line.removeprefix("gitdir: ")).resolve(strict=True)


def _read_reference(git_directory: Path, repository: Path, reference: str) -> str:
    """Read one loose or packed Git reference."""
    loose_reference = git_directory / reference
    if loose_reference.is_file():
        return loose_reference.read_text(encoding="utf-8").strip()
    packed_references = (git_directory / "packed-refs").read_text(encoding="utf-8").splitlines()
    matching_references = [
        line.split(" ", maxsplit=1)[0]
        for line in packed_references
        if not line.startswith(("#", "^")) and line.endswith(f" {reference}")
    ]
    if len(matching_references) != 1:
        message = f"Unable to resolve Git reference {reference!r} in {repository}"
        raise RuntimeError(message)
    return matching_references[0]


def read_repository_revision(repository: Path) -> str:
    """Return the checked-out SHA-1 revision from repository metadata."""
    git_directory = _read_git_directory(repository)
    head_value = (git_directory / "HEAD").read_text(encoding="utf-8").strip()
    if head_value.startswith("ref: "):
        reference = head_value.removeprefix("ref: ")
        head_value = _read_reference(git_directory, repository, reference)
    if len(head_value) != _SHA1_HEX_LENGTH or any(
        character not in "0123456789abcdef" for character in head_value.lower()
    ):
        message = f"Invalid Git revision in {repository}: {head_value!r}"
        raise RuntimeError(message)
    return head_value.lower()


__all__ = ["read_repository_revision"]
