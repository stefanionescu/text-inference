"""Route third-party output to raw capture files while keeping consoles quiet."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
import logging
import warnings
from dataclasses import dataclass

from config.runtime.logging import DEPENDENCY_LOGGER_NAMES, DEPENDENCY_QUIET_ENVIRONMENT

if TYPE_CHECKING:
    from collections.abc import Mapping


@dataclass(slots=True)
class _OutputState:
    """Process-wide dependency output routing state."""

    is_configured: bool = False


_OUTPUT_STATE = _OutputState()


def is_raw_output_enabled(environment: Mapping[str, str] | None = None) -> bool:
    """Return the exact debug-output flag, rejecting ambiguous values."""
    active_environment = os.environ if environment is None else environment
    configured_value = active_environment.get("LOGS_ENABLED", "0")
    if configured_value not in {"0", "1"}:
        message = f"LOGS_ENABLED must be 0 or 1, got {configured_value!r}"
        raise ValueError(message)
    return configured_value == "1"


def _build_capture_sink(log_path: str | None) -> logging.Handler:
    """Create a raw dependency handler or a quiet sink."""
    if log_path == "-":
        return logging.StreamHandler()
    if log_path:
        return logging.FileHandler(log_path, encoding="utf-8")
    return logging.NullHandler()


def configure_dependency_output() -> None:
    """Configure dependency logging before optional GPU libraries import."""
    if _OUTPUT_STATE.is_configured:
        return
    _OUTPUT_STATE.is_configured = True
    if is_raw_output_enabled():
        return
    for name, value in DEPENDENCY_QUIET_ENVIRONMENT.items():
        os.environ.setdefault(name, value)
    warnings.simplefilter("default")
    logging.captureWarnings(capture=True)
    capture_path = os.environ.get("DEPENDENCY_LOG_FILE")
    for logger_name in DEPENDENCY_LOGGER_NAMES:
        dependency_logger = logging.getLogger(logger_name)
        dependency_logger.handlers.clear()
        dependency_logger.addHandler(_build_capture_sink(capture_path))
        dependency_logger.setLevel(logging.DEBUG)
        dependency_logger.propagate = False


__all__ = ["configure_dependency_output", "is_raw_output_enabled"]
