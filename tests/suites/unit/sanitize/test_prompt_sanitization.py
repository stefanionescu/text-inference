"""Unit tests for prompt sanitization."""

from __future__ import annotations

import pytest

from src.text.prompt import sanitize_prompt


def test_prompt_rejects_inputs() -> None:
    """Test sanitize prompt rejects missing, invalid, and oversized values."""
    with pytest.raises(ValueError, match="prompt is required"):
        sanitize_prompt(None)
    with pytest.raises(TypeError, match="prompt must be a string"):
        sanitize_prompt(123)
    with pytest.raises(ValueError, match="prompt is empty after sanitization"):
        sanitize_prompt("")
    with pytest.raises(ValueError, match="prompt is empty after sanitization"):
        sanitize_prompt("   \t\n  ")
    with pytest.raises(ValueError, match="prompt too large"):
        sanitize_prompt("x" * 100, max_chars=50)


def test_prompt_sanitizes_inputs() -> None:
    """Test sanitize prompt keeps valid text and strips unsafe chars."""
    assert sanitize_prompt("hello world") == "hello world"
    result = sanitize_prompt("hello\x00world\x1f!")
    assert "\x00" not in result
    assert "\x1f" not in result
    assert "hello" in result
    result = sanitize_prompt("hello\u202aworld")
    assert "\u202a" not in result
    result = sanitize_prompt('say \\"hello\\"')
    assert '\\"' not in result
