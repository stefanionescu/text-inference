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

from .suffix import compute_tail_lengths
from .cleanup_steps import sanitize_stream_chunk


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
        # Whether the raw tail window has dropped the true stream start
        self._has_trimmed_stream_start = False

    def _sanitize_raw_tail(self) -> str:
        """Sanitize the whole raw tail and record which one-shot steps stay pending.

        Returns:
            The updated text.

        """
        is_prefix_context_active = self._is_prefix_pending or (not self._has_trimmed_stream_start)
        is_capital_context_active = self._is_capital_pending or (not self._has_trimmed_stream_start)
        sanitized, is_prefix_pending, is_capital_pending = sanitize_stream_chunk(
            self._raw_tail,
            is_prefix_pending=is_prefix_context_active,
            is_capital_pending=is_capital_context_active,
            is_leading_whitespace_stripped=is_prefix_context_active,
        )
        self._is_prefix_pending = is_prefix_pending
        self._is_capital_pending = is_capital_pending
        return sanitized

    def push(self, chunk: str) -> str:
        """Process a new raw chunk and return the sanitized delta.

        Args:
            chunk: One piece of streamed text.

        Returns:
            The sanitized delta.

        """
        if not chunk:
            return ""

        self._raw_tail += chunk

        sanitized = self._sanitize_raw_tail()

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
        """Emit any remaining buffered sanitized text.

        Returns:
            The resulting text.

        """
        if not self._raw_tail and not self._sanitized_tail:
            return ""

        sanitized = self._sanitize_raw_tail()

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


def _shared_prefix_length(left_text: str, right_text: str) -> int:
    """Return the shared prefix length of two strings.

    Args:
        left_text: Text of the left.
        right_text: Text of the right.

    Returns:
        The shared prefix length of two strings.

    """
    maximum_length = min(len(left_text), len(right_text))
    index = 0
    while index < maximum_length and left_text[index] == right_text[index]:
        index += 1
    return index


__all__ = ["StreamingSanitizer"]
