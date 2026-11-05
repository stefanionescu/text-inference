"""Unit tests for email and phone verbalization."""

from __future__ import annotations

import pytest

from src.text.verbalize import (
    verbalize_email,
    verbalize_emails,
    verbalize_phone_digit,
    verbalize_phone_number,
    verbalize_phone_numbers,
)


def test_verbalize_email_cases() -> None:
    """Test email verbalization for direct and inline addresses."""
    assert verbalize_email("me@you.com") == "me at you dot com"
    assert verbalize_emails("") == ""
    result = verbalize_emails("reach me@you.com or them@here.org")
    if "me at you dot com" not in result:
        pytest.fail("Assertion failed")
    if "them at here dot org" not in result:
        pytest.fail("Assertion failed")


def test_phone_digit_cases() -> None:
    """Test phone digit verbalization."""
    assert verbalize_phone_digit("+") == "plus"
    assert verbalize_phone_digit("1") == "one"
    assert verbalize_phone_digit("0") == "zero"
    assert verbalize_phone_digit("9") == "nine"
    assert verbalize_phone_digit(" ") == ""
    assert verbalize_phone_digit("-") == ""


def test_phone_number_cases() -> None:
    """Test phone number verbalization and replacement."""
    result = verbalize_phone_number("+1 234")
    if "plus" not in result:
        pytest.fail("Assertion failed")
    if "one" not in result:
        pytest.fail("Assertion failed")
    if "two" not in result:
        pytest.fail("Assertion failed")
    if "three" not in result:
        pytest.fail("Assertion failed")
    if "four" not in result:
        pytest.fail("Assertion failed")
    assert verbalize_phone_numbers("") == ""
    assert verbalize_phone_numbers("no numbers") == "no numbers"
    result = verbalize_phone_numbers("call +1 234 567 8900 now")
    assert "+" not in result or "plus" in result
    # The original phone number should be replaced
    assert "234 567 8900" not in result
