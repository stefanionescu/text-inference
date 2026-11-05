"""Tokenizer checks accept either tokenizer file and explain every failure."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.tokens.validation import validate_tokenizer_exists, require_local_model_directory

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("filenames", "has_json", "has_config"),
    [
        (["tokenizer.json"], True, False),
        (["tokenizer_config.json"], False, True),
        (["tokenizer.json", "tokenizer_config.json"], True, True),
    ],
)
def test_either_tokenizer_file_passes(
    tmp_path: Path,
    filenames: list[str],
    *,
    has_json: bool,
    has_config: bool,
) -> None:
    """One tokenizer file is enough, and the result says which ones exist.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.
        filenames: Names of the files.
        has_json: Whether a JSON exists.
        has_config: Whether a config exists.

    """
    for filename in filenames:
        (tmp_path / filename).write_text("{}", encoding="utf-8")
    result = validate_tokenizer_exists(str(tmp_path))
    assert result.is_valid
    assert result.error_message is None
    assert result.has_tokenizer_json is has_json
    assert result.has_tokenizer_config is has_config


def test_empty_folder_explains_fix(tmp_path: Path) -> None:
    """A folder without tokenizer files names both files that it looked for.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    result = validate_tokenizer_exists(str(tmp_path))
    assert not result.is_valid
    assert result.error_message is not None
    assert "tokenizer.json" in result.error_message
    assert "tokenizer_config.json" in result.error_message


def test_missing_folder_is_invalid(tmp_path: Path) -> None:
    """A path that does not exist fails the check instead of raising.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    result = validate_tokenizer_exists(str(tmp_path / "absent"))
    assert not result.is_valid
    assert result.error_message is not None
    assert "does not exist" in result.error_message


def test_empty_model_path_refused() -> None:
    """An empty path never resolves to the current folder."""
    with pytest.raises(ValueError, match="Model path is empty"):
        require_local_model_directory("")


def test_file_path_is_refused(tmp_path: Path) -> None:
    """A path to a file is not a model folder.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    model_file = tmp_path / "model.bin"
    model_file.write_text("weights", encoding="utf-8")
    with pytest.raises(NotADirectoryError, match="must be a directory"):
        require_local_model_directory(model_file)
