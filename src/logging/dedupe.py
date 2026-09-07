"""Deduplicated logging for inference engines.

This module tracks emitted log keys to avoid repeated operational messages.

Usage:
    from src.logging.dedupe import warn_unique

    warn_unique("cuda_mem", "torch unavailable for CUDA mem introspection")
    warn_unique("cuda_mem", "same warning")
"""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_emitted_keys: set[str] = set()


def warn_unique(key: str, message: str, *, prefix: str = "[config]") -> bool:
    """Emit a warning message only once per key.

    Args:
        key: Unique identifier for this warning type.
        message: The warning message to print.
        prefix: Optional prefix for the message.

    Returns:
        True if the warning was emitted, False if already emitted.

    """
    if key in _emitted_keys:
        return False

    _emitted_keys.add(key)
    full_message = f"{prefix} Warning: {message}" if prefix else f"Warning: {message}"
    logger.warning(full_message)
    return True


def info_unique(key: str, message: str, *, prefix: str = "[config]") -> bool:
    """Emit an info message only once per key.

    Args:
        key: Unique identifier for this message type.
        message: The metadata message to print.
        prefix: Optional prefix for the message.

    Returns:
        True if the message was emitted, False if already emitted.

    """
    if key in _emitted_keys:
        return False

    _emitted_keys.add(key)
    full_message = f"{prefix} {message}" if prefix else message
    logger.info(full_message)
    return True


__all__ = ["info_unique", "warn_unique"]
