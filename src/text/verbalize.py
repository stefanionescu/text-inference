"""Email and phone number verbalization.

This module converts emails and phone numbers to spoken form for
text-to-speech (TTS) output:

- Emails: "me@example.com" becomes "me at example dot com"
- Phones: "+1 234 567 8900" becomes "plus one two three four five six seven eight nine zero zero"

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
    """Convert email to spoken form: me@example.com becomes me at example dot com.

    Args:
        email: Matched email address.

    Returns:
        The address with each `@` and `.` written as a word.

    """
    result = email.replace("@", " at ")
    return result.replace(".", " dot ")


def verbalize_emails(text: str) -> str:
    """Find and verbalize all email addresses in text.

    Args:
        text: Text that can contain email addresses.

    Returns:
        The text with each address in spoken form.

    """
    if not text:
        return ""

    def replace_email(match: re.Match[str]) -> str:
        """Verbalize one matched email address.

        Args:
            match: Match of `EMAIL_PATTERN`.

        Returns:
            The matched address in spoken form.

        """
        return verbalize_email(match.group(0))

    return EMAIL_PATTERN.sub(replace_email, text)


def verbalize_phone_digit(char: str) -> str:
    """Convert a single phone character to spoken form.

    Args:
        char: One character of a phone number.

    Returns:
        The spoken word for `+` or a digit, otherwise an empty string.

    """
    if char == "+":
        return "plus"
    if char in DIGIT_WORDS:
        return DIGIT_WORDS[char]
    return ""


def verbalize_phone_number(raw_number: str) -> str:
    """Convert phone number to spoken form: +1 234 becomes plus one two three four.

    Args:
        raw_number: Phone number as matched in the text.

    Returns:
        The spoken words joined by spaces.

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
        text: Text that can contain international phone numbers.

    Returns:
        The text with each detected number in spoken form.

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
