"""Exact tokenizer-based history accounting."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .tokenizer import ThreadSafeTokenizer


def count_tokens(text: str, tokenizer: ThreadSafeTokenizer) -> int:
    """Count tokens with the configured model tokenizer."""
    if not text:
        return 0
    return tokenizer.count(text)


__all__ = [
    "count_tokens",
]
