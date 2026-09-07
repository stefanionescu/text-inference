"""Prompt selection error type."""

from __future__ import annotations


class PromptSelectionError(ValueError):
    """Raised when prompt selection fails due to invalid parameters."""


__all__ = ["PromptSelectionError"]
