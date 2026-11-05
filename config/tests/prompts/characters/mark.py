"""Mark prompt profile definitions."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..blocks import dislikes
from .builder import personality_blocks, build_character_prompt
from ..blocks.shared import MARK_IDENTITY_BLOCK
from ..personalities import (
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


def _prompt(module: ModuleType, prefix: str, dislikes_text: str, *, voiceprint_prefix: str | None = None) -> str:
    """Build one Mark prompt profile."""
    return build_character_prompt(
        MARK_IDENTITY_BLOCK,
        personality_blocks(module, prefix, voiceprint_prefix=voiceprint_prefix),
        dislikes_text,
    )


MARK_FLIRTY = _prompt(flirty, "FLIRTY", dislikes.MARK_FLIRTY_DISLIKES)
MARK_SAVAGE = _prompt(savage, "SAVAGE", dislikes.MARK_SAVAGE_DISLIKES)
MARK_RELIGIOUS = _prompt(religious, "RELIGIOUS", dislikes.MARK_RELIGIOUS_DISLIKES)
MARK_DELULU = _prompt(delulu, "DELULU", dislikes.MARK_DELULU_DISLIKES)
MARK_SPIRITUAL = _prompt(spiritual, "SPIRITUAL", dislikes.MARK_SPIRITUAL_DISLIKES)
MARK_FOODIE = _prompt(foodie, "FOODIE", dislikes.MARK_FOODIE_DISLIKES)
MARK_WARM = _prompt(warm, "WARM", dislikes.MARK_WARM_DISLIKES)
MARK_HONEST = _prompt(honest, "HONEST", dislikes.MARK_HONEST_DISLIKES)
MARK_BOOMER = _prompt(boomer, "BOOMER", dislikes.MARK_BOOMER_DISLIKES)
MARK_ZOOMER = _prompt(zoomer, "ZOOMER", dislikes.MARK_ZOOMER_DISLIKES)
MARK_EX = _prompt(ex, "EX", dislikes.MARK_EX_DISLIKES)
MARK_KPOP = _prompt(kpop, "KPOP", dislikes.MARK_KPOP_DISLIKES)
MARK_SHOPAHOLIC = _prompt(shopaholic, "SHOPAHOLIC", dislikes.MARK_SHOPAHOLIC_DISLIKES)
MARK_EPERSONA = _prompt(
    epersona,
    "EPERSONA",
    dislikes.MARK_EPERSONA_DISLIKES,
    voiceprint_prefix="EBOY",
)


__all__ = [
    "MARK_BOOMER",
    "MARK_DELULU",
    "MARK_EPERSONA",
    "MARK_EX",
    "MARK_FLIRTY",
    "MARK_FOODIE",
    "MARK_HONEST",
    "MARK_KPOP",
    "MARK_RELIGIOUS",
    "MARK_SAVAGE",
    "MARK_SHOPAHOLIC",
    "MARK_SPIRITUAL",
    "MARK_WARM",
    "MARK_ZOOMER",
]
