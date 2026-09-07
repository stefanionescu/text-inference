"""Input closed error type."""

from __future__ import annotations

from .client import TestClientError


class InputClosedError(TestClientError):
    """Raised when stdin closes (EOF) or user presses Ctrl+C."""


__all__ = ["InputClosedError"]
