"""Unit tests for quiet and raw dependency output routing."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
import logging
import importlib

import pytest

from src.logging import output

if TYPE_CHECKING:
    from pathlib import Path


def test_log_flag_contract() -> None:
    """Test the raw-output switch accepts exact binary values only."""
    assert not output.is_raw_output_enabled({})
    assert not output.is_raw_output_enabled({"LOGS_ENABLED": "0"})
    assert output.is_raw_output_enabled({"LOGS_ENABLED": "1"})
    with pytest.raises(ValueError, match="must be 0 or 1"):
        output.is_raw_output_enabled({"LOGS_ENABLED": "true"})


def test_default_dependency_capture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Test quiet mode routes dependency diagnostics to raw capture."""
    output_module = importlib.reload(output)
    capture_path = tmp_path / "dependencies.log"
    logger_name = "scenario.dependency.capture"
    dependency_logger = logging.getLogger(logger_name)
    original_handlers = dependency_logger.handlers.copy()
    original_level = dependency_logger.level
    original_propagation = dependency_logger.propagate
    is_propagation_configured = True
    monkeypatch.setattr(output_module, "DEPENDENCY_LOGGER_NAMES", (logger_name,))
    monkeypatch.setattr(output_module, "DEPENDENCY_QUIET_ENVIRONMENT", {"SCENARIO_QUIET": "1"})
    monkeypatch.setenv("LOGS_ENABLED", "0")
    monkeypatch.setenv("DEPENDENCY_LOG_FILE", str(capture_path))
    try:
        output_module.configure_dependency_output()
        is_propagation_configured = dependency_logger.propagate
        dependency_logger.warning("third-party diagnostic")
        for destination in dependency_logger.handlers:
            destination.flush()
    finally:
        for destination in dependency_logger.handlers:
            destination.close()
        dependency_logger.handlers = original_handlers
        dependency_logger.setLevel(original_level)
        dependency_logger.propagate = original_propagation

    assert capture_path.read_text(encoding="utf-8").strip() == "third-party diagnostic"
    assert not is_propagation_configured
    assert os.environ["SCENARIO_QUIET"] == "1"


def test_logs_preserve_handlers(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test raw mode leaves dependency logging unsuppressed."""
    output_module = importlib.reload(output)
    logger_name = "scenario.dependency.visible"
    dependency_logger = logging.getLogger(logger_name)
    destination = logging.NullHandler()
    monkeypatch.setattr(dependency_logger, "handlers", [destination])
    monkeypatch.setattr(dependency_logger, "propagate", True)
    monkeypatch.setattr(output_module, "DEPENDENCY_LOGGER_NAMES", (logger_name,))
    monkeypatch.setenv("LOGS_ENABLED", "1")

    output_module.configure_dependency_output()

    assert dependency_logger.handlers == [destination]
    assert dependency_logger.propagate
