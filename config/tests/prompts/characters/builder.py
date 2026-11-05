"""Character prompt construction helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

from config.tests.prompts.blocks import dislikes
from config.tests.prompts.blocks.shared import (
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
from config.tests.prompts.personalities import (
    ex,
    kpop,
    warm,
    boomer,
    delulu,
    flirty,
    foodie,
    honest,
    savage,
    zoomer,
    epersona,
    religious,
    spiritual,
    shopaholic,
)

if TYPE_CHECKING:
    from types import ModuleType

_PERSONALITY_MODULES: dict[str, ModuleType] = {
    "FLIRTY": flirty,
    "SAVAGE": savage,
    "RELIGIOUS": religious,
    "DELULU": delulu,
    "SPIRITUAL": spiritual,
    "FOODIE": foodie,
    "WARM": warm,
    "HONEST": honest,
    "BOOMER": boomer,
    "ZOOMER": zoomer,
    "EX": ex,
    "KPOP": kpop,
    "SHOPAHOLIC": shopaholic,
    "EPERSONA": epersona,
}


@dataclass(frozen=True, slots=True)
class _PersonalityBlocks:
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


def _personality_blocks(
    module: ModuleType,
    prefix: str,
    *,
    voiceprint_prefix: str | None = None,
) -> _PersonalityBlocks:
    """Return all prompt sections for a personality module."""
    voiceprint = voiceprint_prefix or prefix
    return _PersonalityBlocks(
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


def _character_prompt(character_block: str, blocks: _PersonalityBlocks, dislikes_text: str) -> str:
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
{dislikes_text}
{blocks.features}
{blocks.boundaries}
{USER_PROFILE_BLOCK}
User's Local Time and Date:
4:20PM, December 13th 2025, late afternoon.
"""


def build_character_prompts(character: str, identity_block: str, *, epersona_voiceprint: str) -> dict[str, str]:
    """Return one character's full prompt for every personality, keyed by the personality's block prefix."""
    voiceprint_prefixes = {"EPERSONA": epersona_voiceprint}
    return {
        prefix: _character_prompt(
            identity_block,
            _personality_blocks(module, prefix, voiceprint_prefix=voiceprint_prefixes.get(prefix)),
            _text_block(dislikes, f"{character}_{prefix}_DISLIKES"),
        )
        for prefix, module in _PERSONALITY_MODULES.items()
    }


__all__ = ["build_character_prompts"]
