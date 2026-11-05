"""Environment readers return usable values and never crash on bad input."""

from __future__ import annotations

import math

import pytest

from src.runtime.environment import read_environment_text, read_environment_float, read_environment_integer

_VARIABLE = "TEXT_INFERENCE_TEST_VARIABLE"
_DEFAULT_INTEGER = 7
_DEFAULT_FLOAT = 1.5


def _set_variable(monkeypatch: pytest.MonkeyPatch, raw_value: str | None) -> None:
    """Set the test variable, or remove it when the case has no value.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        raw_value: Text to store, or None to leave the variable unset.

    """
    monkeypatch.delenv(_VARIABLE, raising=False)
    if raw_value is not None:
        monkeypatch.setenv(_VARIABLE, raw_value)


@pytest.mark.parametrize(
    ("raw_value", "expected"), [("42", 42), ("not-a-number", _DEFAULT_INTEGER), (None, _DEFAULT_INTEGER)]
)
def test_integer_reader_uses_default(monkeypatch: pytest.MonkeyPatch, raw_value: str | None, expected: int) -> None:
    """An absent or malformed integer gives the default instead of an exception.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        raw_value: Unvalidated value as received.
        expected: Value that the test expects.

    """
    _set_variable(monkeypatch, raw_value)
    assert read_environment_integer(_VARIABLE, _DEFAULT_INTEGER) == expected


@pytest.mark.parametrize(
    ("raw_value", "expected"), [("2.5", 2.5), ("not-a-number", _DEFAULT_FLOAT), (None, _DEFAULT_FLOAT)]
)
def test_float_reader_uses_default(monkeypatch: pytest.MonkeyPatch, raw_value: str | None, expected: float) -> None:
    """An absent or malformed float gives the default instead of an exception.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        raw_value: Unvalidated value as received.
        expected: Value that the test expects.

    """
    _set_variable(monkeypatch, raw_value)
    assert math.isclose(read_environment_float(_VARIABLE, _DEFAULT_FLOAT), expected)


@pytest.mark.parametrize(
    ("raw_value", "default_text", "expected"),
    [("set", "unused", "set"), ("", "chosen", "chosen"), (None, "chosen", "chosen"), (None, None, "")],
)
def test_text_reader_ignores_empty(
    monkeypatch: pytest.MonkeyPatch,
    raw_value: str | None,
    default_text: str | None,
    expected: str,
) -> None:
    """An empty value counts as unset, and the result is always a string.

    Args:
        monkeypatch: Pytest fixture that patches objects for one test.
        raw_value: Unvalidated value as received.
        default_text: Text of the default.
        expected: Value that the test expects.

    """
    _set_variable(monkeypatch, raw_value)
    assert read_environment_text(_VARIABLE, default_text) == expected
