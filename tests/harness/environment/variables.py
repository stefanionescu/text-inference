"""Environment variable parsing for test clients.

Provides typed accessors for reading configuration from environment variables
with fallback defaults. Used by test runners and config modules.
"""

from __future__ import annotations

import os


def read_environment_integer(key: str, default: int) -> int:
    """Read an integer from an environment variable with a fallback."""
    raw_value = os.getenv(key)
    if raw_value is None:
        return default
    try:
        return int(raw_value)
    except ValueError:
        return default


def read_environment_float(key: str, default: float) -> float:
    """Read a float from an environment variable with a fallback."""
    raw_value = os.getenv(key)
    if raw_value is None:
        return default
    try:
        return float(raw_value)
    except ValueError:
        return default


__all__ = [
    "read_environment_float",
    "read_environment_integer",
]
