"""Startup validation refuses bad deployments and reports every problem it finds."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.runtime.settings import read_settings
from src.runtime.validation import validate_settings

if TYPE_CHECKING:
    from pathlib import Path


def _valid_environment(model_folder: Path) -> dict[str, str]:
    """Build the environment of a deployment that passes startup validation.

    Args:
        model_folder: Folder of the model.

    Returns:
        The environment of a deployment that passes startup validation.

    """
    (model_folder / "tokenizer.json").write_text("{}", encoding="utf-8")
    return {
        "API_KEY": "test-key",
        "MAX_CONCURRENT_CONNECTIONS": "4",
        "MODEL": str(model_folder),
        "INFERENCE_ENGINE": "trt",
    }


def _validation_message(environment: dict[str, str]) -> str:
    """Return the error that startup validation raises for an environment.

    Args:
        environment: Environment variables to read.

    Returns:
        The error that startup validation raises for an environment.

    """
    with pytest.raises(ValueError, match=r".+") as error:
        validate_settings(read_settings(environment=environment))
    return str(error.value)


def test_valid_settings_pass(tmp_path: Path) -> None:
    """A complete deployment environment starts without any error.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    validate_settings(read_settings(environment=_valid_environment(tmp_path)))


@pytest.mark.parametrize(
    ("setting_name", "raw_value", "expected_error"),
    [
        ("MAX_CONCURRENT_CONNECTIONS", "0", "MAX_CONCURRENT_CONNECTIONS must be a positive integer"),
        ("INFERENCE_ENGINE", "unknown", "INFERENCE_ENGINE must be"),
        ("KV_DTYPE", "unknown", "KV_DTYPE must be one of"),
        ("TRT_DTYPE", "unknown", "TRT_DTYPE must be one of"),
        ("TRT_MAX_BATCH_SIZE", "0", "TRT_MAX_BATCH_SIZE must be positive"),
        ("RUNTIME_QUANTIZATION", "unknown", "Invalid RUNTIME_QUANTIZATION='unknown' for trt"),
        ("TEMPERATURE", "99", "TEMPERATURE must be"),
        ("TOP_P", "99", "TOP_P must be"),
        ("TOP_K", "100000", "TOP_K must be"),
        ("MIN_P", "99", "MIN_P must be"),
        ("REPETITION_PENALTY", "99", "REPETITION_PENALTY must be"),
        ("PRESENCE_PENALTY", "99", "PRESENCE_PENALTY must be"),
        ("FREQUENCY_PENALTY", "99", "FREQUENCY_PENALTY must be"),
        ("WEBSOCKET_IDLE_TIMEOUT_SECONDS", "0", "WEBSOCKET_IDLE_TIMEOUT_SECONDS must be"),
        ("GENERATION_TIMEOUT_SECONDS", "0", "GENERATION_TIMEOUT_SECONDS must be"),
        ("GPU_MEMORY_FRACTION", "2", "GPU_MEMORY_FRACTION must be"),
    ],
)
def test_bad_setting_reports_error(
    tmp_path: Path,
    setting_name: str,
    raw_value: str,
    expected_error: str,
) -> None:
    """Each out-of-range or unknown value stops startup and names its setting.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.
        setting_name: Name of the setting.
        raw_value: Unvalidated value as received.
        expected_error: Expected error.

    """
    environment = _valid_environment(tmp_path)
    environment[setting_name] = raw_value
    assert expected_error in _validation_message(environment)


@pytest.mark.parametrize(
    ("setting_name", "expected_error"),
    [
        ("MAX_CONCURRENT_CONNECTIONS", "MAX_CONCURRENT_CONNECTIONS environment variable is required"),
        ("MODEL", "MODEL is required"),
    ],
)
def test_absent_setting_reports_error(tmp_path: Path, setting_name: str, expected_error: str) -> None:
    """A required setting that the deployment leaves out stops startup.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.
        setting_name: Name of the setting.
        expected_error: Expected error.

    """
    environment = _valid_environment(tmp_path)
    del environment[setting_name]
    assert expected_error in _validation_message(environment)


def test_missing_tokenizer_stops_startup(tmp_path: Path) -> None:
    """A model folder without tokenizer files fails before any engine loads.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    environment = _valid_environment(tmp_path)
    (tmp_path / "tokenizer.json").unlink()
    assert "MODEL tokenizer validation failed" in _validation_message(environment)


def test_all_errors_reported_together(tmp_path: Path) -> None:
    """An operator sees every bad setting in one failure, not one per restart.

    Args:
        tmp_path: Pytest fixture that provides a temporary folder.

    """
    environment = _valid_environment(tmp_path)
    environment["KV_DTYPE"] = "unknown"
    environment["TEMPERATURE"] = "99"
    message = _validation_message(environment)
    assert "KV_DTYPE must be one of" in message
    assert "TEMPERATURE must be" in message
