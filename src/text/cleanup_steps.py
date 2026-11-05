"""Stateless text cleanup steps that the streaming sanitizer runs on each pass."""

from __future__ import annotations

import re
import html

from config.text.verbalization import OH_MAX_H_COUNT, OH_MAX_O_COUNT

from .patterns import (
    EMOJI_PATTERN,
    EMDASH_PATTERN,
    DOT_RUN_PATTERN,
    PERCENT_PATTERN,
    ELLIPSIS_PATTERN,
    EMOTICON_PATTERN,
    HTML_TAG_PATTERN,
    SUBTRACTION_PATTERN,
    WORD_HYPHEN_PATTERN,
    ACTION_EMOTE_PATTERN,
    DEGREE_SYMBOL_PATTERN,
    NEWLINE_TOKEN_PATTERN,
    DEGREES_KELVIN_PATTERN,
    EXAGGERATED_OH_PATTERN,
    SPACED_DOT_RUN_PATTERN,
    COLLAPSE_SPACES_PATTERN,
    DEGREES_CELSIUS_PATTERN,
    NEGATIVE_NUMBER_PATTERN,
    DOUBLE_DOT_SPACE_PATTERN,
    FREESTYLE_PREFIX_PATTERN,
    DEGREES_FAHRENHEIT_PATTERN,
    SPACE_BEFORE_PUNCT_PATTERN,
    SINGLE_LETTER_SUFFIX_PATTERN,
    ELLIPSIS_TRAILING_DOT_PATTERN,
    LEADING_NEWLINE_TOKENS_PATTERN,
    ELLIPSIS_TRAILING_SPACE_PATTERN,
    _strip_escaped_quotes,
)
from .verbalize import verbalize_emails, verbalize_phone_numbers


def _apply_leading_capital_stream(text: str, *, is_capital_pending: bool) -> tuple[str, bool]:
    """Streaming-friendly leading capital enforcement.

    Returns the transformed text and whether capitalization is still pending.

    Args:
        text: Text to process.
        is_capital_pending: Whether capital is pending.

    Returns:
        The resulting items.

    """
    if not is_capital_pending:
        return text, False
    for index, char in enumerate(text):
        if char.isalpha():
            if char.islower():
                return f"{text[:index]}{char.upper()}{text[index + 1 :]}", False
            return text, False
    return text, True


def _apply_stream_prefix(text: str) -> str:
    """Remove leading freestyle prefixes from streamed output.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    cleaned = FREESTYLE_PREFIX_PATTERN.sub("", text, count=1)
    if cleaned != text:
        cleaned = cleaned.lstrip()
    return _strip_leading_newline_tokens(cleaned)


def _normalize_stream_dots(text: str) -> str:
    """Normalize ellipsis and dot spacing in streamed text.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    cleaned = ELLIPSIS_PATTERN.sub("...", text)
    cleaned = NEWLINE_TOKEN_PATTERN.sub(" ", cleaned)
    cleaned = DOUBLE_DOT_SPACE_PATTERN.sub("...", cleaned)
    cleaned = ELLIPSIS_TRAILING_DOT_PATTERN.sub("...", cleaned)
    cleaned = ELLIPSIS_TRAILING_SPACE_PATTERN.sub("...", cleaned)
    cleaned = DOT_RUN_PATTERN.sub("...", cleaned)
    cleaned = SPACED_DOT_RUN_PATTERN.sub(".", cleaned)
    return re.sub(r"(?<!\.)\.(?!\.)(?=[A-Za-z0-9])", ". ", cleaned)


def _verbalize_units(text: str) -> str:
    """Verbalize temperature, degree, and percentage symbols.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    cleaned = DEGREES_FAHRENHEIT_PATTERN.sub(" degrees Fahrenheit", text)
    cleaned = DEGREES_CELSIUS_PATTERN.sub(" degrees Celsius", cleaned)
    cleaned = DEGREES_KELVIN_PATTERN.sub(" degrees Kelvin", cleaned)
    cleaned = DEGREE_SYMBOL_PATTERN.sub(" degrees", cleaned)
    return PERCENT_PATTERN.sub(" percent", cleaned)


def _normalize_dashes(text: str) -> str:
    """Normalize dash-like tokens into spoken text or spaces.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    cleaned = SUBTRACTION_PATTERN.sub(r"\1 minus \2", text)
    cleaned = NEGATIVE_NUMBER_PATTERN.sub(r" minus \1", cleaned)
    cleaned = SINGLE_LETTER_SUFFIX_PATTERN.sub(r"\1\2", cleaned)
    cleaned = WORD_HYPHEN_PATTERN.sub(r"\1 \2", cleaned)
    return EMDASH_PATTERN.sub(" ", cleaned)


def _strip_markup_symbols(text: str) -> str:
    """Remove markup, escaped quotes, and unsupported symbols.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    cleaned = text.replace("'", "'")
    cleaned = SPACE_BEFORE_PUNCT_PATTERN.sub(r"\1", cleaned)
    cleaned = _strip_escaped_quotes(cleaned)
    cleaned = EXAGGERATED_OH_PATTERN.sub(_normalize_exaggerated_oh, cleaned)
    cleaned = _strip_emoji_like_tokens(cleaned)
    cleaned = HTML_TAG_PATTERN.sub("", cleaned)
    return html.unescape(cleaned)


def _normalize_exaggerated_oh(match: re.Match[str]) -> str:
    """Normalize exaggerated oh/ooh spellings.

    Args:
        match: Regular expression match to rewrite.

    Returns:
        The updated text.

    """
    text = match.group(0)
    oh_character_count = sum(1 for char in text if char.lower() == "o")
    h_character_count = sum(1 for char in text if char.lower() == "h")
    if oh_character_count <= OH_MAX_O_COUNT and h_character_count <= OH_MAX_H_COUNT:
        return text
    return "Ooh" if text[0].isupper() else "ooh"


def _strip_leading_newline_tokens(text: str) -> str:
    """Remove leading newline tokens without inserting padding.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    if not text:
        return ""
    return LEADING_NEWLINE_TOKENS_PATTERN.sub("", text)


def _collapse_spaces(text: str) -> str:
    """Collapse runs of spaces/tabs into a single space.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    if not text:
        return ""
    return COLLAPSE_SPACES_PATTERN.sub(" ", text)


def _strip_asterisks(text: str) -> str:
    """Remove asterisk markers used for emphasis.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    if not text:
        return ""
    return text.replace("*", " ")


def _strip_emoji_like_tokens(text: str) -> str:
    """Remove unicode emojis and ASCII emoticons while collapsing spacing.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    if not text:
        return ""
    text = EMOJI_PATTERN.sub(" ", text)
    text = EMOTICON_PATTERN.sub(" ", text)
    return _collapse_spaces(text)


def _sanitize_stream_text(text: str) -> str:
    """Apply the core stream text sanitization pipeline.

    Args:
        text: Text to process.

    Returns:
        The updated text.

    """
    cleaned = verbalize_emails(text)
    cleaned = verbalize_phone_numbers(cleaned)
    cleaned = ACTION_EMOTE_PATTERN.sub("", cleaned)
    cleaned = _strip_asterisks(cleaned)
    cleaned = _normalize_stream_dots(cleaned)
    cleaned = _verbalize_units(cleaned)
    cleaned = _normalize_dashes(cleaned)
    cleaned = _strip_markup_symbols(cleaned)
    return _collapse_spaces(cleaned)


def sanitize_stream_chunk(
    text: str,
    *,
    is_prefix_pending: bool,
    is_capital_pending: bool,
    is_leading_whitespace_stripped: bool,
) -> tuple[str, bool, bool]:
    """Run the streaming sanitization pipeline on a single chunk.

    Args:
        text: Text to process.
        is_prefix_pending: Whether prefix is pending.
        is_capital_pending: Whether capital is pending.
        is_leading_whitespace_stripped: Whether leading whitespace is stripped.

    Returns:
        The resulting items.

    """
    if not text:
        return "", is_prefix_pending, is_capital_pending

    cleaned = text
    if is_prefix_pending:
        cleaned = _apply_stream_prefix(cleaned)
        is_prefix_pending = False

    cleaned = _sanitize_stream_text(cleaned)
    cleaned, is_capital_pending = _apply_leading_capital_stream(cleaned, is_capital_pending=is_capital_pending)

    if is_leading_whitespace_stripped:
        cleaned = cleaned.lstrip()

    return cleaned, is_prefix_pending, is_capital_pending


__all__ = ["sanitize_stream_chunk"]
