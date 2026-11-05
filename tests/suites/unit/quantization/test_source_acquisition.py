"""Source acquisition pins an immutable revision and calls the real Hub API correctly."""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import TYPE_CHECKING, cast
import inspect
from unittest.mock import Mock

import pytest
import huggingface_hub

from src.quantization import source

if TYPE_CHECKING:
    from pathlib import Path
    from collections.abc import Callable

_COMMIT = "a" * 40
_MODEL = "example/model"
_REAL_DOWNLOAD = cast("Callable[..., object]", huggingface_hub.snapshot_download)


def _stub_hub(monkeypatch: pytest.MonkeyPatch, snapshot_path: Path, sha: object = _COMMIT) -> Mock:
    """Replace the Hub calls and return the snapshot download double.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        snapshot_path: Path of the snapshot.
        sha: Sha.

    Returns:
        The snapshot download double.

    """
    record = SimpleNamespace(sha=sha)
    monkeypatch.setattr(source, "HfApi", Mock(return_value=Mock(model_info=Mock(return_value=record))))
    download = Mock(return_value=str(snapshot_path))
    monkeypatch.setattr(source, "_DOWNLOAD_SNAPSHOT", download)
    return download


def test_download_matches_hub_signature(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The snapshot call uses keywords that the installed huggingface_hub accepts.

    A double accepts any keyword, so binding to the real signature catches a renamed argument.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    download = _stub_hub(monkeypatch, tmp_path)
    source.acquire_source(_MODEL, "main", token="hub-token", cache_folder="/cache")
    keywords = download.call_args.kwargs
    inspect.signature(_REAL_DOWNLOAD).bind(**keywords)
    assert keywords["cache_dir"] == "/cache"


def test_download_pins_resolved_commit(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The download uses the commit the Hub resolved, not the moving branch name.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    download = _stub_hub(monkeypatch, tmp_path)
    snapshot = source.acquire_source(_MODEL, "main", token=None, cache_folder=None)
    assert download.call_args.kwargs["revision"] == _COMMIT
    assert snapshot.identity.kind == source.HUB_SOURCE_KIND
    assert snapshot.identity.requested_revision == "main"
    assert snapshot.identity.resolved_revision == _COMMIT
    assert snapshot.path == tmp_path.resolve()


@pytest.mark.parametrize("sha", [None, "main", "abc123"])
def test_mutable_revision_is_refused(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, sha: object) -> None:
    """A revision that is not a full commit never reaches the download.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        tmp_path: Pytest fixture that provides a temporary folder.
        sha: Sha.

    """
    download = _stub_hub(monkeypatch, tmp_path, sha=sha)
    with pytest.raises(ValueError, match="immutable model revision"):
        source.acquire_source(_MODEL, "main", token=None, cache_folder=None)
    download.assert_not_called()


def test_local_identity_tracks_changes(tmp_path: Path) -> None:
    """A local folder's identity is stable until a checkpoint file changes.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    config_path = tmp_path / "config.json"
    config_path.write_text("{}", encoding="utf-8")
    first = source.acquire_source(str(tmp_path), "main", token=None, cache_folder=None)
    repeated = source.acquire_source(str(tmp_path), "main", token=None, cache_folder=None)
    assert first.identity == repeated.identity
    assert first.identity.kind == source.LOCAL_SOURCE_KIND
    assert first.identity.requested_revision is None
    assert first.identity.resolved_revision.startswith("local:")
    config_path.write_text('{"changed": true}', encoding="utf-8")
    changed = source.acquire_source(str(tmp_path), "main", token=None, cache_folder=None)
    assert changed.identity.resolved_revision != first.identity.resolved_revision


def test_empty_local_folder_refused(tmp_path: Path) -> None:
    """A folder without checkpoint files has no identity to pin.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    with pytest.raises(ValueError, match="does not contain checkpoint files"):
        source.acquire_source(str(tmp_path), "main", token=None, cache_folder=None)


def test_file_model_is_refused(tmp_path: Path) -> None:
    """A path to a file is refused before any Hub call.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    model_file = tmp_path / "model.bin"
    model_file.write_text("weights", encoding="utf-8")
    with pytest.raises(NotADirectoryError, match="must be a directory"):
        source.acquire_source(str(model_file), "main", token=None, cache_folder=None)


def test_identity_reads_snapshot_folder(tmp_path: Path) -> None:
    """A Hub snapshot's identity comes from its commit-named folder.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    snapshot_folder = tmp_path / _COMMIT
    snapshot_folder.mkdir()
    identity = source.derive_source_identity(_MODEL, snapshot_folder, "main")
    assert identity.kind == source.HUB_SOURCE_KIND
    assert identity.resolved_revision == _COMMIT


def test_identity_refuses_branch_folder(tmp_path: Path) -> None:
    """A snapshot folder that a branch name labels has no immutable identity.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    snapshot_folder = tmp_path / "main"
    snapshot_folder.mkdir()
    with pytest.raises(ValueError, match="does not contain a commit revision"):
        source.derive_source_identity(_MODEL, snapshot_folder, "main")


def test_identity_of_local_model(tmp_path: Path) -> None:
    """A local model keeps its local identity regardless of the snapshot path.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    (tmp_path / "config.json").write_text("{}", encoding="utf-8")
    identity = source.derive_source_identity(str(tmp_path), tmp_path, "main")
    assert identity.kind == source.LOCAL_SOURCE_KIND


def test_command_prints_snapshot_path(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """The command passes the environment through and prints only the snapshot path.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        capsys: Pytest fixture that captures standard output and standard error.
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    download = _stub_hub(monkeypatch, tmp_path)
    monkeypatch.setitem(os.environ, "HF_TOKEN", "hub-token")
    monkeypatch.setitem(os.environ, "HUGGINGFACE_HUB_CACHE", "/cache")
    assert source.main(["--model", _MODEL]) == 0
    assert capsys.readouterr().out.strip() == str(tmp_path.resolve())
    assert download.call_args.kwargs["token"] == "hub-token"
    assert download.call_args.kwargs["cache_dir"] == "/cache"
