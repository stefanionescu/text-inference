"""Shared validation helpers for message handlers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from src.errors import ValidationError
from config.limits import PERSONALITY_MAX_LENGTH
from src.text.prompt import sanitize_prompt
from src.text.patterns import LETTERS_ONLY_PATTERN
from config.prompt.profiles import VALID_GENDERS

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True)
class PromptLimit:
    """Prompt validation policy for a single text field."""

    field_label: str
    invalid_error_code: str
    too_long_error_code: str
    maximum_tokens: int
    count_tokens: Callable[[str], int]


def normalize_gender(value: str | None) -> str | None:
    """Normalize gender input to standardized values ('female'|'male')."""
    if value is None:
        return None
    normalized_value = value.strip().lower()
    return normalized_value if normalized_value in VALID_GENDERS else None


def is_gender_blank(value: str | None) -> bool:
    """Check if gender is empty or null (before normalization)."""
    return value is None or not value.strip()


def normalize_personality(value: str | None) -> str | None:
    """Normalize personality: letters-only, length-limited, lowercased."""
    if value is None:
        return None
    normalized_value = value.strip()
    is_invalid = (
        not normalized_value
        or len(normalized_value) > PERSONALITY_MAX_LENGTH
        or not LETTERS_ONLY_PATTERN.match(normalized_value)
    )
    if is_invalid:
        return None
    return normalized_value.lower()


def is_personality_blank(value: str | None) -> bool:
    """Check if personality is empty or null (before normalization)."""
    return value is None or not value.strip()


def validate_required_gender(raw_gender: str | None) -> str:
    """Validate and normalize the required gender field."""
    if is_gender_blank(raw_gender):
        message = "missing_gender"
        raise ValidationError(
            message,
            "gender is required and cannot be empty",
        )
    gender = normalize_gender(raw_gender)
    if gender is None:
        message = "invalid_gender"
        raise ValidationError(
            message,
            "gender must be 'female' or 'male'",
        )
    return gender


def validate_required_personality(raw_personality: str | None) -> str:
    """Validate and normalize the required personality field."""
    if is_personality_blank(raw_personality):
        message = "missing_personality"
        raise ValidationError(
            message,
            "personality is required and cannot be empty",
        )
    normalized = normalize_personality(raw_personality)
    if normalized is None:
        message = "invalid_personality"
        raise ValidationError(
            message,
            f"personality must be letters-only and lower than or equal to {PERSONALITY_MAX_LENGTH} characters",
        )
    return normalized


def require_prompt(
    raw_prompt: str | None,
    *,
    error_code: str,
    message: str,
) -> str:
    """Return a present prompt or raise a validation error."""
    if not raw_prompt:
        raise ValidationError(error_code, message)
    return raw_prompt


def sanitize_prompt_limit(raw_prompt: str, limit: PromptLimit) -> str:
    """Sanitize a prompt and enforce its token limit."""
    try:
        prompt = sanitize_prompt(raw_prompt)
    except ValueError as exception:
        raise ValidationError(limit.invalid_error_code, str(exception)) from exception

    if limit.count_tokens(prompt) > limit.maximum_tokens:
        raise ValidationError(
            limit.too_long_error_code,
            f"{limit.field_label} exceeds token limit ({limit.maximum_tokens})",
        )
    return prompt


__all__ = [
    "PromptLimit",
    "ValidationError",
    "is_gender_blank",
    "is_personality_blank",
    "normalize_gender",
    "normalize_personality",
    "require_prompt",
    "sanitize_prompt_limit",
    "validate_required_gender",
    "validate_required_personality",
]
