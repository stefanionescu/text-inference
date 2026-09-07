"""Test client error root."""

from __future__ import annotations


class TestClientError(Exception):
    """Root type for test client errors."""


__all__ = ["TestClientError"]
