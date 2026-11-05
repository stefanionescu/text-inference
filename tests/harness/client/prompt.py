"""Prompt profile selection for test clients."""

from __future__ import annotations

from tests.harness.client.errors import PromptSelectionError
from config.tests.prompts.detailed import PROMPT_PROFILES


def normalize_gender(value: str | None) -> str:
    """Normalize an assistant gender to its protocol token.

    Args:
        value: Value to check or convert.

    Returns:
        The updated text.

    """
    if not value:
        return ""
    return value.strip().lower()


def select_prompt(gender: str | None, personality: str | None) -> str:
    """Select the exact prompt for a gender and personality pair.

    Args:
        gender: Name of the gender profile.
        personality: Name of the personality profile.

    Returns:
        The exact prompt for a gender and personality pair.

    Raises:
        PromptSelectionError: Gender is required for prompt selection.

    """
    normalized_gender = normalize_gender(gender)
    normalized_personality = (personality or "").strip().lower()
    if not normalized_gender:
        message = "Gender is required for prompt selection"
        raise PromptSelectionError(message)
    if not normalized_personality:
        message = "Personality is required for prompt selection"
        raise PromptSelectionError(message)

    key = (normalized_gender, normalized_personality)
    profile = PROMPT_PROFILES.get(key)
    if profile is None:
        available = ", ".join(
            f"{item_gender}/{item_personality}" for item_gender, item_personality in sorted(PROMPT_PROFILES)
        )
        message = f"No prompt found for '{normalized_gender}/{normalized_personality}'. Available: {available}"
        raise PromptSelectionError(message)
    prompt = profile["prompt"]
    if not prompt.strip():
        message = f"Prompt for '{normalized_gender}/{normalized_personality}' is empty"
        raise PromptSelectionError(message)
    return prompt


__all__ = ["PromptSelectionError", "normalize_gender", "select_prompt"]
