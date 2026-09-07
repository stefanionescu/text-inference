"""Unit tests for sampling parameter extraction and validation."""

from __future__ import annotations

import pytest
from src.errors import ValidationError
from src.messages.sampling import extract_sampling_overrides


def test_sampling_success() -> None:
    """Test sampling extraction accepts supported payload shapes."""
    temperature = 0.5
    top_k = 7

    assert extract_sampling_overrides({}) == {}
    assert extract_sampling_overrides({"temperature": str(temperature)})["temperature"] == temperature
    assert extract_sampling_overrides({"sampling": {"top_k": float(top_k)}})["top_k"] == top_k
    assert extract_sampling_overrides({"sanitize_output": False})["sanitize_output"] is False


def test_sampling_errors() -> None:
    """Test sampling extraction rejects invalid payload shapes."""
    with pytest.raises(ValidationError, match="temperature must be between"):
        extract_sampling_overrides({"temperature": 999.0})
    with pytest.raises(ValidationError, match="temperature must be a valid"):
        extract_sampling_overrides({"temperature": True})
    with pytest.raises(ValidationError, match="top_k must be a valid"):
        extract_sampling_overrides({"top_k": 1.5})
    with pytest.raises(ValidationError, match="sampling must be an object"):
        extract_sampling_overrides({"sampling": "not_a_dict"})
