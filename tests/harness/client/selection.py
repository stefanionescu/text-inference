"""Message selection utilities for test scripts.

This module provides helpers for selecting user messages from CLI arguments
or fallback sequences. Used by warmup, benchmark, and other test clients
that accept optional user-provided messages.
"""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence


def choose_message(
    words: list[str],
    fallback: str,
    *,
    defaults: Sequence[str] | None = None,
    rng: random.Random | None = None,
) -> str:
    """Select a message based on user-provided tokens or fallbacks.

    Priority order:
    1. Joined words from CLI arguments (if provided and non-empty)
    2. Random selection from defaults (if provided)
    3. Static fallback string

    Args:
        words: Tokens captured from CLI arguments (for example, the remaining command line).
        fallback: Default string used when no tokens/defaults are available.
        defaults: Optional sequence of canned messages to sample from.
        rng: Optional random generator to make deterministic choices in tests.

    Returns:
        Selected message string.

    Examples:
        >>> choose_message(["hello", "world"], "default")
        'hello world'
        >>> choose_message([], "default", defaults=["opt1", "opt2"])  # random
        'opt1'  # or 'opt2'
        >>> choose_message([], "fallback")
        'fallback'

    """
    if words:
        candidate = " ".join(words).strip()
        if candidate:
            return candidate

    if defaults:
        chooser = rng or random
        return chooser.choice(list(defaults))

    return fallback


__all__ = ["choose_message"]
