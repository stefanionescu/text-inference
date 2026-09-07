"""Unit tests for sampling parameter extraction and validation."""

from __future__ import annotations
import pytest
from src.errors import ValidationError
from src.messages.sampling import extract_sampling_overrides
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS


def test_sampling_success() -> None:
    """Test sampling extraction accepts supported payload shapes."""
    temperature = 0.5
    top_k = 7

    assert extract_sampling_overrides({}, sampling_settings=DEFAULT_APPLICATION_SETTINGS.sampling) == {}
    assert (
        extract_sampling_overrides(
            {"temperature": str(temperature)}, sampling_settings=DEFAULT_APPLICATION_SETTINGS.sampling
        )["temperature"]
        == temperature
    )
    assert (
        extract_sampling_overrides(
            {"sampling": {"top_k": float(top_k)}}, sampling_settings=DEFAULT_APPLICATION_SETTINGS.sampling
        )["top_k"]
        == top_k
    )
    assert (
        extract_sampling_overrides({"sanitize_output": False}, sampling_settings=DEFAULT_APPLICATION_SETTINGS.sampling)[
            "sanitize_output"
        ]
        is False
    )


def test_sampling_errors() -> None:
    """Test sampling extraction rejects invalid payload shapes."""
    with pytest.raises(ValidationError, match="temperature must be between"):
        extract_sampling_overrides({"temperature": 999.0}, sampling_settings=DEFAULT_APPLICATION_SETTINGS.sampling)
    with pytest.raises(ValidationError, match="temperature must be a valid"):
        extract_sampling_overrides({"temperature": True}, sampling_settings=DEFAULT_APPLICATION_SETTINGS.sampling)
    with pytest.raises(ValidationError, match="top_k must be a valid"):
        extract_sampling_overrides({"top_k": 1.5}, sampling_settings=DEFAULT_APPLICATION_SETTINGS.sampling)
    with pytest.raises(ValidationError, match="sampling must be an object"):
        extract_sampling_overrides({"sampling": "not_a_dict"}, sampling_settings=DEFAULT_APPLICATION_SETTINGS.sampling)
