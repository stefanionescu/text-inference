"""Unit tests for message validation helpers."""

from __future__ import annotations

import pytest
from src.errors import ValidationError
from src.messages.validators import PromptLimit, sanitize_prompt_limit

# --- sanitize_prompt_limit ---


def test_prompt_limit_validation() -> None:
    """Test prompt limit validation success and failures."""
    result = sanitize_prompt_limit(
        "hello world",
        PromptLimit(
            field_label="prompt",
            invalid_error_code="invalid_prompt",
            too_long_error_code="prompt_too_long",
            maximum_tokens=100,
            count_tokens=lambda text: len(text.split()),
        ),
    )
    assert result == "hello world"
    with pytest.raises(ValidationError):
        sanitize_prompt_limit(
            "",
            PromptLimit(
                field_label="prompt",
                invalid_error_code="invalid_prompt",
                too_long_error_code="prompt_too_long",
                maximum_tokens=100,
                count_tokens=lambda text: len(text.split()),
            ),
        )
    with pytest.raises(ValidationError, match="exceeds token limit"):
        sanitize_prompt_limit(
            "hello world foo bar",
            PromptLimit(
                field_label="prompt",
                invalid_error_code="invalid_prompt",
                too_long_error_code="prompt_too_long",
                maximum_tokens=2,
                count_tokens=lambda text: len(text.split()),
            ),
        )
