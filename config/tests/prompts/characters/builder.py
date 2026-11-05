"""Character prompt construction helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from ..blocks.shared import (
    AVOID_BLOCK,
    LANGUAGE_BLOCK,
    KNOWLEDGE_BLOCK,
    PUNCTUATION_BLOCK,
    USER_PROFILE_BLOCK,
    DRAFTING_HELP_BLOCK,
    MESSAGE_LENGTH_BLOCK,
    USER_ADDRESSING_BLOCK,
    REALITY_CONSTRAINTS_BLOCK,
)

if TYPE_CHECKING:
    from types import ModuleType


@dataclass(frozen=True, slots=True)
class PersonalityBlocks:
    """Prompt sections for one personality variant."""

    voiceprint: str
    sexual_tone: str
    traits: str
    messages: str
    helpfulness: str
    quirks: str
    likes: str
    features: str
    boundaries: str


def _text_block(module: ModuleType, name: str) -> str:
    """Return a named text block from a personality module."""
    value = getattr(module, name)
    if not isinstance(value, str):
        message = f"{module.__name__}.{name} must be a string"
        raise TypeError(message)
    return value


def personality_blocks(
    module: ModuleType,
    prefix: str,
    *,
    voiceprint_prefix: str | None = None,
) -> PersonalityBlocks:
    """Return all prompt sections for a personality module."""
    voiceprint = voiceprint_prefix or prefix
    return PersonalityBlocks(
        voiceprint=_text_block(module, f"{voiceprint}_VOICEPRINT_BLOCK"),
        sexual_tone=_text_block(module, f"{prefix}_SEXUAL_TONE_BLOCK"),
        traits=_text_block(module, f"{prefix}_TRAITS_BLOCK"),
        messages=_text_block(module, f"{prefix}_MESSAGES_BLOCK"),
        helpfulness=_text_block(module, f"{prefix}_HELPFULNESS_BLOCK"),
        quirks=_text_block(module, f"{prefix}_QUIRKS_BLOCK"),
        likes=_text_block(module, f"{prefix}_LIKES_BLOCK"),
        features=_text_block(module, f"{prefix}_FEATURES_BLOCK"),
        boundaries=_text_block(module, f"{prefix}_BOUNDARIES_BLOCK"),
    )


def build_character_prompt(character_block: str, blocks: PersonalityBlocks, dislikes: str) -> str:
    """Build a full character prompt from shared and personality blocks."""
    return f"""{MESSAGE_LENGTH_BLOCK}
{REALITY_CONSTRAINTS_BLOCK}
{KNOWLEDGE_BLOCK}
{DRAFTING_HELP_BLOCK}
{USER_ADDRESSING_BLOCK}
{LANGUAGE_BLOCK}
{PUNCTUATION_BLOCK}
{AVOID_BLOCK}
{character_block}
{blocks.voiceprint}
{blocks.sexual_tone}
{blocks.traits}
{blocks.messages}
{blocks.helpfulness}
{blocks.quirks}
{blocks.likes}
Dislikes:
{dislikes}
{blocks.features}
{blocks.boundaries}
{USER_PROFILE_BLOCK}
User's Local Time and Date:
4:20PM, December 13th 2025, late afternoon.
"""


__all__ = ["PersonalityBlocks", "build_character_prompt", "personality_blocks"]
