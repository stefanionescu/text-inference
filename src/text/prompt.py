"""Prompt sanitization utilities for user-provided text.

This module performs a one-shot cleanup of inbound prompts:
    - Type validation and non-empty enforcement
    - Unicode normalization (NFKC) and mojibake repair
    - Control and bidi character stripping
    - Escaped quote stripping
    - Optional size limiting (for bounded fields)
"""

from __future__ import annotations

import unicodedata

from .patterns import BIDI_CHAR_PATTERN, CTRL_CHAR_PATTERN, _strip_escaped_quotes

try:
    from ftfy import fix_text as _ftfy_fix_text
except ImportError:
    _ftfy_fix_text = None


def sanitize_prompt(raw: object | None, *, max_chars: int | None = None) -> str:
    """Sanitize user-provided prompt text.

    Args:
        raw: Input prompt value.
        max_chars: Optional post-sanitization character limit.

    Returns:
        The updated text.

    Raises:
        TypeError: Prompt must be a string.
        ValueError: Prompt is required.

    """
    if raw is None:
        message = "prompt is required"
        raise ValueError(message)
    if not isinstance(raw, str):
        message = "prompt must be a string"
        raise TypeError(message)

    # Normalize and fix encoding issues
    text = _ftfy_fix_text(raw) if callable(_ftfy_fix_text) else raw
    text = unicodedata.normalize("NFKC", text)

    # Remove disallowed controls, bidi markers, and escaped quotes
    text = CTRL_CHAR_PATTERN.sub("", text)
    text = BIDI_CHAR_PATTERN.sub("", text)
    text = _strip_escaped_quotes(text)

    text = text.strip()
    if not text:
        message = "prompt is empty after sanitization"
        raise ValueError(message)
    if max_chars is not None and len(text) > max_chars:
        message = "prompt too large"
        raise ValueError(message)
    return text


__all__ = ["sanitize_prompt"]
