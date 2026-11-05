"""Streaming sanitizer for assistant outputs.

This sanitizer is stateful and operates on streamed model text. It:
    - Strips freestyle prefixes and leading newline tokens once
    - Verbalizes emails/phone numbers
    - Normalizes ellipses/dashes/quotes/spacing
    - Removes escaped quotes, emojis/emoticons, and HTML tags
    - Enforces a leading capital once
    - Buffers unstable suffixes (ellipsis, partial words/entities) to avoid
      emitting incomplete tokens mid-stream
"""

from __future__ import annotations

import re
import html

from config.text.verbalization import OH_MAX_H_COUNT, OH_MAX_O_COUNT

from .suffix import compute_tail_lengths
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


class StreamingSanitizer:
    """Stateful sanitizer that emits stable chunks for streaming."""

    # How much suffix (in characters) we keep as a "potentially unstable" buffer
    # so boundary-sensitive validators (emails, phone numbers, ellipsis, html)
    # can operate across streamed chunks.
    _MAXIMUM_TAIL_LENGTH = 64

    def __init__(self) -> None:
        """Initialize streaming sanitizer state."""
        # Raw tail retained for boundary-sensitive checks
        self._raw_tail: str = ""
        # Sanitized tail retained but not yet emitted
        self._sanitized_tail: str = ""
        # Sanitized stable parts already emitted
        self._emitted_parts: list[str] = []
        # Flags for one-shot behaviors
        self._is_prefix_pending = True
        self._is_capital_pending = True
        # Whether we've dropped the true stream start from the raw tail window
        self._has_trimmed_stream_start = False

    def push(self, chunk: str) -> str:
        """Process a new raw chunk and return the sanitized delta."""
        if not chunk:
            return ""

        self._raw_tail += chunk

        is_prefix_context_active = self._is_prefix_pending or (not self._has_trimmed_stream_start)
        is_capital_context_active = self._is_capital_pending or (not self._has_trimmed_stream_start)
        sanitized, is_prefix_pending, is_capital_pending = _sanitize_stream_chunk(
            self._raw_tail,
            is_prefix_pending=is_prefix_context_active,
            is_capital_pending=is_capital_context_active,
            is_leading_whitespace_stripped=is_prefix_context_active,
        )
        self._is_prefix_pending = is_prefix_pending
        self._is_capital_pending = is_capital_pending

        stable_length, tail_length = compute_tail_lengths(
            raw_tail=self._raw_tail,
            sanitized=sanitized,
            maximum_tail_length=self._MAXIMUM_TAIL_LENGTH,
        )

        delta = ""
        if stable_length > 0:
            stable = sanitized[:stable_length]
            emitted_text = "".join(self._emitted_parts)
            shared_prefix_length = _shared_prefix_length(emitted_text, stable)
            if shared_prefix_length < len(emitted_text):
                emitted_text = emitted_text[:shared_prefix_length]
                self._emitted_parts = [emitted_text] if emitted_text else []
            delta = stable[shared_prefix_length:]

            if delta:
                self._emitted_parts.append(delta)

        self._sanitized_tail = sanitized[stable_length : stable_length + tail_length]

        return delta

    def flush(self) -> str:
        """Emit any remaining buffered sanitized text."""
        if not self._raw_tail and not self._sanitized_tail:
            return ""

        is_prefix_context_active = self._is_prefix_pending or (not self._has_trimmed_stream_start)
        is_capital_context_active = self._is_capital_pending or (not self._has_trimmed_stream_start)
        sanitized, is_prefix_pending, is_capital_pending = _sanitize_stream_chunk(
            self._raw_tail,
            is_prefix_pending=is_prefix_context_active,
            is_capital_pending=is_capital_context_active,
            is_leading_whitespace_stripped=is_prefix_context_active,
        )
        self._is_prefix_pending = is_prefix_pending
        self._is_capital_pending = is_capital_pending

        emitted_text = "".join(self._emitted_parts)
        shared_prefix_length = _shared_prefix_length(emitted_text, sanitized)
        if shared_prefix_length < len(emitted_text):
            emitted_text = emitted_text[:shared_prefix_length]
            self._emitted_parts = [emitted_text] if emitted_text else []
        tail = sanitized[shared_prefix_length:].rstrip()

        if tail:
            self._emitted_parts.append(tail)
        self._sanitized_tail = ""
        self._raw_tail = ""
        self._has_trimmed_stream_start = False
        return tail


def _apply_leading_capital_stream(text: str, *, is_capital_pending: bool) -> tuple[str, bool]:
    """Streaming-friendly leading capital enforcement.

    Returns the transformed text and whether capitalization is still pending.
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
    """Remove leading freestyle prefixes from streamed output."""
    cleaned = FREESTYLE_PREFIX_PATTERN.sub("", text, count=1)
    if cleaned != text:
        cleaned = cleaned.lstrip()
    return _strip_leading_newline_tokens(cleaned)


def _normalize_stream_dots(text: str) -> str:
    """Normalize ellipsis and dot spacing in streamed text."""
    cleaned = ELLIPSIS_PATTERN.sub("...", text)
    cleaned = NEWLINE_TOKEN_PATTERN.sub(" ", cleaned)
    cleaned = DOUBLE_DOT_SPACE_PATTERN.sub("...", cleaned)
    cleaned = ELLIPSIS_TRAILING_DOT_PATTERN.sub("...", cleaned)
    cleaned = ELLIPSIS_TRAILING_SPACE_PATTERN.sub("...", cleaned)
    cleaned = DOT_RUN_PATTERN.sub("...", cleaned)
    cleaned = SPACED_DOT_RUN_PATTERN.sub(".", cleaned)
    return re.sub(r"(?<!\.)\.(?!\.)(?=[A-Za-z0-9])", ". ", cleaned)


def _verbalize_units(text: str) -> str:
    """Verbalize temperature, degree, and percentage symbols."""
    cleaned = DEGREES_FAHRENHEIT_PATTERN.sub(" degrees Fahrenheit", text)
    cleaned = DEGREES_CELSIUS_PATTERN.sub(" degrees Celsius", cleaned)
    cleaned = DEGREES_KELVIN_PATTERN.sub(" degrees Kelvin", cleaned)
    cleaned = DEGREE_SYMBOL_PATTERN.sub(" degrees", cleaned)
    return PERCENT_PATTERN.sub(" percent", cleaned)


def _normalize_dashes(text: str) -> str:
    """Normalize dash-like tokens into spoken text or spaces."""
    cleaned = SUBTRACTION_PATTERN.sub(r"\1 minus \2", text)
    cleaned = NEGATIVE_NUMBER_PATTERN.sub(r" minus \1", cleaned)
    cleaned = SINGLE_LETTER_SUFFIX_PATTERN.sub(r"\1\2", cleaned)
    cleaned = WORD_HYPHEN_PATTERN.sub(r"\1 \2", cleaned)
    return EMDASH_PATTERN.sub(" ", cleaned)


def _strip_markup_symbols(text: str) -> str:
    """Remove markup, escaped quotes, and unsupported symbols."""
    cleaned = text.replace("'", "'")
    cleaned = SPACE_BEFORE_PUNCT_PATTERN.sub(r"\1", cleaned)
    cleaned = _strip_escaped_quotes(cleaned)
    cleaned = EXAGGERATED_OH_PATTERN.sub(_normalize_exaggerated_oh, cleaned)
    cleaned = _strip_emoji_like_tokens(cleaned)
    cleaned = HTML_TAG_PATTERN.sub("", cleaned)
    return html.unescape(cleaned)


def _sanitize_stream_text(text: str) -> str:
    """Apply the core stream text sanitization pipeline."""
    cleaned = verbalize_emails(text)
    cleaned = verbalize_phone_numbers(cleaned)
    cleaned = ACTION_EMOTE_PATTERN.sub("", cleaned)
    cleaned = _strip_asterisks(cleaned)
    cleaned = _normalize_stream_dots(cleaned)
    cleaned = _verbalize_units(cleaned)
    cleaned = _normalize_dashes(cleaned)
    cleaned = _strip_markup_symbols(cleaned)
    return _collapse_spaces(cleaned)


def _sanitize_stream_chunk(
    text: str,
    *,
    is_prefix_pending: bool,
    is_capital_pending: bool,
    is_leading_whitespace_stripped: bool,
) -> tuple[str, bool, bool]:
    """Run the streaming sanitization pipeline on a single chunk."""
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


def _shared_prefix_length(left_text: str, right_text: str) -> int:
    """Return the shared prefix length of two strings."""
    maximum_length = min(len(left_text), len(right_text))
    index = 0
    while index < maximum_length and left_text[index] == right_text[index]:
        index += 1
    return index


def _normalize_exaggerated_oh(match: re.Match[str]) -> str:
    """Normalize exaggerated oh/ooh spellings."""
    text = match.group(0)
    oh_character_count = sum(1 for char in text if char.lower() == "o")
    h_character_count = sum(1 for char in text if char.lower() == "h")
    if oh_character_count <= OH_MAX_O_COUNT and h_character_count <= OH_MAX_H_COUNT:
        return text
    return "Ooh" if text[0].isupper() else "ooh"


def _strip_leading_newline_tokens(text: str) -> str:
    """Remove leading newline tokens without inserting padding."""
    if not text:
        return ""
    return LEADING_NEWLINE_TOKENS_PATTERN.sub("", text)


def _collapse_spaces(text: str) -> str:
    """Collapse runs of spaces/tabs into a single space."""
    if not text:
        return ""
    return COLLAPSE_SPACES_PATTERN.sub(" ", text)


def _strip_asterisks(text: str) -> str:
    """Remove asterisk markers used for emphasis."""
    if not text:
        return ""
    return text.replace("*", " ")


def _strip_emoji_like_tokens(text: str) -> str:
    """Remove unicode emojis and ASCII emoticons while collapsing spacing."""
    if not text:
        return ""
    text = EMOJI_PATTERN.sub(" ", text)
    text = EMOTICON_PATTERN.sub(" ", text)
    return _collapse_spaces(text)


__all__ = ["StreamingSanitizer"]
