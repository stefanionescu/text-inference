"""Checkpoint upload commands keep their flags and call the real Hub API correctly."""

from __future__ import annotations

import os
from types import SimpleNamespace
from typing import TYPE_CHECKING
import inspect
from unittest.mock import Mock

import pytest
from huggingface_hub import HfApi
from huggingface_hub.errors import HfHubHTTPError

from src.hf import trt, vllm, upload
from src.hf import license as hf_license

if TYPE_CHECKING:
    from types import ModuleType
    from pathlib import Path

_REPOSITORY = "example/model-quantized"
_CARD_TEXT = "# Model card\n"
_REVISION = "a" * 40


def _stub_upload_steps(monkeypatch: pytest.MonkeyPatch, module: ModuleType) -> Mock:
    """Replace validation and the Hub client, and return the Hub client double.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        module: Python module to read.

    Returns:
        The Hub client double.

    """
    client = Mock()
    monkeypatch.setattr(upload, "HfApi", Mock(return_value=client))
    monkeypatch.setattr(module, "validate_checkpoint", Mock())
    monkeypatch.setattr(module, "require_provenance", Mock(return_value={}))
    monkeypatch.setattr(module, "build_model_card", Mock(return_value=_CARD_TEXT))
    monkeypatch.setitem(os.environ, "HF_TOKEN", "hub-token")
    return client


def _stub_model_record(monkeypatch: pytest.MonkeyPatch, **card_fields: str) -> None:
    """Make the Hub return a model record with these model-card fields.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        **card_fields: Card fields.

    """
    record = SimpleNamespace(card_data=SimpleNamespace(**card_fields))
    monkeypatch.setattr(hf_license, "HfApi", Mock(return_value=Mock(model_info=Mock(return_value=record))))


def test_vllm_command_uploads_checkpoint(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    tmp_path: Path,
) -> None:
    """The vLLM command writes the card, then uploads with keywords the real client accepts.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        capsys: Pytest fixture that captures standard output and standard error.
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    client = _stub_upload_steps(monkeypatch, vllm)
    assert vllm.main(["--checkpoint-dir", str(tmp_path), "--repo-id", _REPOSITORY, "--private"]) == 0
    assert (tmp_path / "README.md").read_text(encoding="utf-8") == _CARD_TEXT
    inspect.signature(HfApi.create_repo).bind(client, **client.create_repo.call_args.kwargs)
    inspect.signature(HfApi.upload_folder).bind(client, **client.upload_folder.call_args.kwargs)
    assert client.create_repo.call_args.kwargs["private"] is True
    assert client.upload_folder.call_args.kwargs["folder_path"] == tmp_path.resolve()
    assert _REPOSITORY in capsys.readouterr().out


def test_trt_command_uploads_checkpoint(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """The TensorRT command puts the requested format in its commit message.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    client = _stub_upload_steps(monkeypatch, trt)
    arguments = ["--checkpoint-dir", str(tmp_path), "--repo-id", _REPOSITORY, "--format", "int4_awq"]
    assert trt.main(arguments) == 0
    assert client.create_repo.call_args.kwargs["private"] is False
    assert "int4_awq" in client.upload_folder.call_args.kwargs["commit_message"]


def test_trt_command_requires_format(tmp_path: Path) -> None:
    """Only the TensorRT command needs --format.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    with pytest.raises(SystemExit):
        trt.main(["--checkpoint-dir", str(tmp_path), "--repo-id", _REPOSITORY])


def test_missing_checkpoint_is_refused(tmp_path: Path) -> None:
    """A checkpoint path that does not exist stops before any Hub call.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    with pytest.raises(FileNotFoundError):
        upload.require_checkpoint_folder(str(tmp_path / "absent"))


def test_file_checkpoint_is_refused(tmp_path: Path) -> None:
    """A checkpoint path must be a folder.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    checkpoint_file = tmp_path / "model.bin"
    checkpoint_file.write_text("weights", encoding="utf-8")
    with pytest.raises(NotADirectoryError, match="must be a directory"):
        upload.require_checkpoint_folder(str(checkpoint_file))


def test_local_source_default_license() -> None:
    """A local source never asks the Hub for a license."""
    license_metadata = hf_license.read_license("model", "local", _REVISION, hf_token=None)
    assert license_metadata.identifier == hf_license.DEFAULT_LICENSE


def test_card_license_fields_copied(monkeypatch: pytest.MonkeyPatch) -> None:
    """A source model card's license carries over to the published card.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.

    """
    _stub_model_record(monkeypatch, license="apache-2.0", license_name=" Apache ", license_link="https://example.com/l")
    license_metadata = hf_license.read_license("example/model", "hub", _REVISION, hf_token=None)
    assert license_metadata.identifier == "apache-2.0"
    assert license_metadata.name == "Apache"
    assert license_metadata.link == "https://example.com/l"


def test_license_name_uses_identifier(monkeypatch: pytest.MonkeyPatch) -> None:
    """A card without a license name or link still links back to the source revision.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.

    """
    _stub_model_record(monkeypatch, license="mit")
    license_metadata = hf_license.read_license("example/model", "hub", _REVISION, hf_token=None)
    assert license_metadata.name == "mit"
    assert _REVISION in license_metadata.link


def test_absent_license_uses_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """A source model card with no license gets the default license.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.

    """
    _stub_model_record(monkeypatch, license="  ")
    license_metadata = hf_license.read_license("example/model", "hub", _REVISION, hf_token=None)
    assert license_metadata.identifier == hf_license.DEFAULT_LICENSE
    assert _REVISION in license_metadata.link


@pytest.mark.parametrize("failure", [OSError("network"), ValueError("bad"), HfHubHTTPError("denied", response=Mock())])
def test_hub_failure_default_license(monkeypatch: pytest.MonkeyPatch, failure: Exception) -> None:
    """A Hub failure never blocks publishing, and the card gets the default license.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        failure: Failure.

    """
    monkeypatch.setattr(hf_license, "HfApi", Mock(return_value=Mock(model_info=Mock(side_effect=failure))))
    license_metadata = hf_license.read_license("example/model", "hub", _REVISION, hf_token=None)
    assert license_metadata.identifier == hf_license.DEFAULT_LICENSE
