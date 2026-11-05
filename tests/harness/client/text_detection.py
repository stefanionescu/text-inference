"""Streaming text completion detection."""

from __future__ import annotations

_TRAILING_CHARS = {'"', "'", ")", "]", "}"}


def contains_complete_sentence(text: str) -> bool:
    """Return True if the text contains a complete sentence terminator.

    Args:
        text: Text to process.

    Returns:
        True if the text contains a complete sentence terminator.

    """
    for index, char in enumerate(text):
        if char not in ".!?":
            continue
        cursor = index + 1
        while cursor < len(text) and text[cursor] in _TRAILING_CHARS:
            cursor += 1
        if cursor >= len(text) or text[cursor].isspace():
            return True
    return False


def has_minimum_word_count(text: str, minimum_words: int) -> bool:
    """Return whether text has the minimum whitespace-delimited word count.

    Args:
        text: Text to process.
        minimum_words: Smallest allowed words.

    Returns:
        Whether text has the minimum whitespace-delimited word count.

    """
    return len(text.strip().split()) >= minimum_words


__all__ = ["contains_complete_sentence", "has_minimum_word_count"]
