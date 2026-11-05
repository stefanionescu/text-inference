"""Unit tests for streaming suffix stability detectors."""

from __future__ import annotations

from src.text.suffix import (
    email_suffix_length,
    phone_suffix_length,
    compute_tail_lengths,
    emoticon_suffix_length,
    html_tag_suffix_length,
    unstable_suffix_length,
    html_entity_suffix_length,
)

TRAILING_DOTS_LENGTH = 3
EXPECTED_STABLE_LENGTH = 3
MAXIMUM_TAIL_LENGTH = 10

# --- unstable_suffix_len ---


def test_unstable_suffix_detection() -> None:
    """Trailing spaces, tabs, and dots stay unstable, while text ending in a letter has no unstable suffix."""
    assert unstable_suffix_length("hello   ") > 0
    assert unstable_suffix_length("hello\t\t") > 0
    assert unstable_suffix_length("hello...") == TRAILING_DOTS_LENGTH
    assert unstable_suffix_length("hello") == 0


# --- html_entity_suffix_len ---


def test_html_entity_suffix() -> None:
    """Test html entity suffix detection."""
    assert html_entity_suffix_length("text &amp") > 0
    assert html_entity_suffix_length("text &amp;") == 0
    assert html_entity_suffix_length("plain text") == 0


# --- html_tag_suffix_len ---


def test_html_tag_suffix() -> None:
    """Test html tag suffix detection."""
    assert html_tag_suffix_length("text <div") > 0
    assert html_tag_suffix_length("text <div>") == 0
    assert html_tag_suffix_length("I <3 you") == 0
    assert html_tag_suffix_length("") == 0


# --- email_suffix_len ---


def test_email_suffix_detection() -> None:
    """A trailing address or partial domain stays unstable, while address-free and empty text report zero."""
    result = email_suffix_length("contact me@you.com")
    assert result > 0
    result = email_suffix_length("contact user@domain")
    assert result > 0
    assert email_suffix_length("no email here!") == 0
    assert email_suffix_length("") == 0


# --- phone_suffix_len ---


def test_phone_suffix_detection() -> None:
    """A trailing international number stays unstable, while digit-free and empty text report zero."""
    assert phone_suffix_length("call me +1 234") > 0
    assert phone_suffix_length("no phone here!") == 0
    assert phone_suffix_length("") == 0


# --- emoticon_suffix_len ---


def test_emoticon_suffix_detection() -> None:
    """An unfinished emoticon such as ``:-``, ``<``, ``X``, or ``^_`` stays unstable; empty text reports zero."""
    assert emoticon_suffix_length("hello :") > 0
    assert emoticon_suffix_length("hello :-") > 0
    assert emoticon_suffix_length("I love you <") > 0
    assert emoticon_suffix_length("haha X") > 0
    assert emoticon_suffix_length("yay ^_") > 0
    assert emoticon_suffix_length("") == 0


# --- compute_tail_lengths ---


def test_compute_tail_lengths() -> None:
    """Test stable and unstable tail length calculations."""
    stable_text_length, tail_text_length = compute_tail_lengths("", "", maximum_tail_length=64)
    assert stable_text_length == 0
    assert tail_text_length == 0
    stable_text_length, tail_text_length = compute_tail_lengths("ok!", "ok!", maximum_tail_length=64)
    assert stable_text_length == EXPECTED_STABLE_LENGTH
    assert tail_text_length == 0
    text = "x" + " " * 100
    stable_text_length, tail_text_length = compute_tail_lengths(text, text, maximum_tail_length=MAXIMUM_TAIL_LENGTH)
    assert tail_text_length <= MAXIMUM_TAIL_LENGTH
    assert stable_text_length + tail_text_length == len(text)
