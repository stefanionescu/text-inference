"""Email and phone number verbalization.

This module converts emails and phone numbers to spoken form for
TTS-friendly output:

- Emails: "me@example.com" → "me at example dot com"
- Phones: "+1 234 567 8900" → "plus one two three four five six seven eight nine zero zero"

Phone number detection uses libphonenumber to identify international
format numbers (+XX country code required).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from phonenumbers import PhoneNumberMatcher

from config.text.verbalization import DIGIT_WORDS

from .patterns import EMAIL_PATTERN

if TYPE_CHECKING:
    import re


def verbalize_email(email: str) -> str:
    """Convert email to spoken form: me@you.com → me at you dot com.

    Args:
        email: Email address text.

    Returns:
        The updated text.

    """
    result = email.replace("@", " at ")
    return result.replace(".", " dot ")


def verbalize_emails(text: str) -> str:
    """Find and verbalize all email addresses in text.

    Args:
        text: Text to process.

    Returns:
        And verbalize all email addresses in text.

    """
    if not text:
        return ""

    def replace_email(match: re.Match[str]) -> str:
        """Verbalize one matched email address.

        Args:
            match: Regular expression match to rewrite.

        Returns:
            The updated text.

        """
        return verbalize_email(match.group(0))

    return EMAIL_PATTERN.sub(replace_email, text)


def verbalize_phone_digit(char: str) -> str:
    """Convert a single phone character to spoken form.

    Args:
        char: One character of text.

    Returns:
        The updated text.

    """
    if char == "+":
        return "plus"
    if char in DIGIT_WORDS:
        return DIGIT_WORDS[char]
    return ""


def verbalize_phone_number(raw_number: str) -> str:
    """Convert phone number to spoken form: +1 234 → plus one two three four.

    Args:
        raw_number: Unvalidated number as received.

    Returns:
        The updated text.

    """
    words: list[str] = []
    for char in raw_number:
        word = verbalize_phone_digit(char)
        if word:
            words.append(word)
    return " ".join(words)


def verbalize_phone_numbers(text: str) -> str:
    """Find and verbalize phone numbers with international format (+XX...).

    Uses libphonenumber to detect phone numbers. Only matches international
    format with explicit + country code (region=None).

    Args:
        text: Text to process.

    Returns:
        And verbalize phone numbers with international format (+XX...).

    """
    if not text:
        return text

    matches = [
        (match.start, match.end, verbalize_phone_number(match.raw_string)) for match in PhoneNumberMatcher(text, None)
    ]

    if not matches:
        return text

    # Replace from end to start to preserve positions
    matches.sort(key=lambda x: x[0], reverse=True)
    result = text
    for start, end, verbalized in matches:
        result = result[:start] + verbalized + result[end:]

    return result


__all__ = [
    "verbalize_email",
    "verbalize_emails",
    "verbalize_phone_digit",
    "verbalize_phone_number",
    "verbalize_phone_numbers",
]
