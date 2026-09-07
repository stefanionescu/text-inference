"""Environment variable parsing."""

from __future__ import annotations

import os


def read_environment_integer(name: str, default: int) -> int:
    """Parse an integer from an environment variable."""
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except (TypeError, ValueError):
        return default


def read_environment_float(name: str, default: float) -> float:
    """Parse a float from an environment variable."""
    raw_value = os.environ.get(name)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except (TypeError, ValueError):
        return default


def read_environment_text(name: str, default: str | None = None) -> str:
    """Read a string from an environment variable."""
    value = os.getenv(name, "")
    return value or default or ""


__all__ = [
    "read_environment_float",
    "read_environment_integer",
    "read_environment_text",
]
