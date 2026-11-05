"""Suffix length detection for streaming stability.

This module computes how much of a streaming text suffix should be
buffered to avoid emitting incomplete patterns:

- Trailing unstable characters (partial words, ellipsis)
- Partial HTML entities (&amp;)
- Unclosed HTML tags (<div)
- Partial email addresses (user@domain)
- Partial phone numbers (+1 234)

By retaining these suffixes, the StreamingSanitizer can process
boundary-sensitive patterns across chunk boundaries.
"""

from __future__ import annotations

import re

from .patterns import EMAIL_PATTERN, TRAILING_STREAM_UNSTABLE_CHARS


def unstable_suffix_length(text: str) -> int:
    """Compute length of trailing unstable characters.

    Includes trailing whitespace, partial ellipsis (dots), and other
    characters that may change when more text arrives.

    Args:
        text: Text to process.

    Returns:
        Length of trailing unstable characters.

    """
    index = len(text)
    while index > 0 and text[index - 1] in TRAILING_STREAM_UNSTABLE_CHARS:
        index -= 1
    # Keep any trailing run of dots (partial ellipsis)
    while index > 0 and text[index - 1] == ".":
        index -= 1
    return len(text) - index


def html_entity_suffix_length(text: str) -> int:
    """Compute length of partial HTML entity at end.

    Matches patterns like "&amp" (incomplete entity).

    Args:
        text: Text to process.

    Returns:
        Length of partial HTML entity at end.

    """
    match = re.search(r"&[A-Za-z]{0,10}$", text)
    if not match:
        return 0
    return len(text) - match.start()


def html_tag_suffix_length(raw_text: str) -> int:
    """Compute length to retain if last '<' is not closed.

    Returns 0 if:
    - The last '<' has a matching '>' after it
    - The '<' is followed by a digit (e.g., '<3' heart emoticon, not a tag)

    Args:
        raw_text: Unvalidated text as received.

    Returns:
        Length to retain if last '<' is not closed.

    """
    suffix_length = 0
    last_opening_index = raw_text.rfind("<") if raw_text else -1
    last_closing_index = raw_text.rfind(">") if raw_text else -1
    is_closed = last_closing_index > last_opening_index
    is_heart = last_opening_index + 1 < len(raw_text) and raw_text[last_opening_index + 1].isdigit()
    if last_opening_index != -1 and not is_closed and not is_heart:
        suffix_length = min(len(raw_text) - last_opening_index, 256)
    return suffix_length


def email_suffix_length(raw_text: str) -> int:
    """Compute length to retain for partial email detection.

    Keeps trailing characters that could form a valid email
    across chunk boundaries.

    Args:
        raw_text: Unvalidated text as received.

    Returns:
        Length to retain for partial email detection.

    """
    if not raw_text:
        return 0
    # Common case: if the tail already has a full email, keep nothing extra
    if EMAIL_PATTERN.search(raw_text):
        # Still keep a small guard in case of partial second email
        return min(16, len(raw_text))

    # Partial email guard (local@ or local@domain)
    partial_match = re.search(r"[A-Za-z0-9._%+-]+@?[A-Za-z0-9.-]*$", raw_text)
    if not partial_match:
        return 0
    return min(len(raw_text) - partial_match.start(), 256)


def phone_suffix_length(raw_text: str) -> int:
    """Compute length to retain for partial phone number detection.

    Keeps trailing digits/+/-/spaces that could form a phone number.

    Args:
        raw_text: Unvalidated text as received.

    Returns:
        Length to retain for partial phone number detection.

    """
    if not raw_text:
        return 0
    partial_match = re.search(r"[+\d][\d \-\(\)]*$", raw_text)
    if not partial_match:
        return 0
    return min(len(raw_text) - partial_match.start(), 64)


def emoticon_suffix_length(text: str) -> int:
    """Compute length to retain for partial emoticon detection.

    Keeps trailing characters that could form a complete emoticon
    across chunk boundaries. This prevents emitting partial emoticons
    like ':' or ':-' that should be stripped when completed as ':-)'

    Args:
        text: Text to process.

    Returns:
        Length to retain for partial emoticon detection.

    """
    if not text:
        return 0
    # Match potential partial emoticons at end of text:
    # - Eyes only: : = ; 8
    # - Eyes + nose: :- ;- =- :^ ;^ =^
    # - Eyes + space (could be followed by emoticon): " :"
    # - Potential heart: <
    # - Potential XD: X or x at end
    partial_match = re.search(
        r"(?:"
        r"[:=;8][-^]?|"  # Eyes with optional nose (no mouth yet)
        r"<|"  # Potential heart <3
        r"[xX](?![a-zA-Z])|"  # Potential XD
        r"\^_?|"  # Potential ^_^
        r"[tT]_?"  # Potential T_T
        r")$",
        text,
    )
    if not partial_match:
        return 0
    return len(text) - partial_match.start()


def compute_tail_lengths(
    raw_tail: str,
    sanitized: str,
    maximum_tail_length: int,
) -> tuple[int, int]:
    """Compute how much of the sanitized text is stable vs tail to buffer.

    Returns ``(stable_length, tail_length)`` where the first value is safe to
    emit and the second must remain buffered.

    Args:
        raw_tail: Unvalidated tail as received.
        sanitized: Text after sanitization.
        maximum_tail_length: Largest allowed tail length.

    Returns:
        How much of the sanitized text is stable vs tail to buffer.

    """
    if not sanitized:
        return 0, 0

    unstable_length = unstable_suffix_length(sanitized)
    html_entity_length = html_entity_suffix_length(sanitized)
    html_tag_length = html_tag_suffix_length(raw_tail)
    email_length = email_suffix_length(raw_tail)
    phone_length = phone_suffix_length(raw_tail)
    emoticon_length = emoticon_suffix_length(raw_tail)

    tail_length = min(
        len(sanitized),
        max(unstable_length, html_entity_length, html_tag_length, email_length, phone_length, emoticon_length, 0),
    )
    stable_length = len(sanitized) - tail_length

    # Bound the retained tail to avoid unbounded buffering
    if tail_length > maximum_tail_length:
        stable_length = len(sanitized) - maximum_tail_length
        tail_length = maximum_tail_length

    return stable_length, tail_length


__all__ = [
    "compute_tail_lengths",
    "email_suffix_length",
    "emoticon_suffix_length",
    "html_entity_suffix_length",
    "html_tag_suffix_length",
    "phone_suffix_length",
    "unstable_suffix_length",
]
