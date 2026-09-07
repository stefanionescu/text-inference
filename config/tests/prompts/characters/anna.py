"""Anna prompt profile definitions."""

from __future__ import annotations

from ..blocks import dislikes
from typing import TYPE_CHECKING
from ..blocks.shared import ANNA_IDENTITY_BLOCK
from .builder import build_character_prompt, personality_blocks
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
    """Build one Anna prompt profile."""
    return build_character_prompt(
        ANNA_IDENTITY_BLOCK,
        personality_blocks(module, prefix, voiceprint_prefix=voiceprint_prefix),
        dislikes_text,
    )


ANNA_FLIRTY = _prompt(flirty, "FLIRTY", dislikes.ANNA_FLIRTY_DISLIKES)
ANNA_SAVAGE = _prompt(savage, "SAVAGE", dislikes.ANNA_SAVAGE_DISLIKES)
ANNA_RELIGIOUS = _prompt(religious, "RELIGIOUS", dislikes.ANNA_RELIGIOUS_DISLIKES)
ANNA_DELULU = _prompt(delulu, "DELULU", dislikes.ANNA_DELULU_DISLIKES)
ANNA_SPIRITUAL = _prompt(spiritual, "SPIRITUAL", dislikes.ANNA_SPIRITUAL_DISLIKES)
ANNA_FOODIE = _prompt(foodie, "FOODIE", dislikes.ANNA_FOODIE_DISLIKES)
ANNA_WARM = _prompt(warm, "WARM", dislikes.ANNA_WARM_DISLIKES)
ANNA_HONEST = _prompt(honest, "HONEST", dislikes.ANNA_HONEST_DISLIKES)
ANNA_BOOMER = _prompt(boomer, "BOOMER", dislikes.ANNA_BOOMER_DISLIKES)
ANNA_ZOOMER = _prompt(zoomer, "ZOOMER", dislikes.ANNA_ZOOMER_DISLIKES)
ANNA_EX = _prompt(ex, "EX", dislikes.ANNA_EX_DISLIKES)
ANNA_KPOP = _prompt(kpop, "KPOP", dislikes.ANNA_KPOP_DISLIKES)
ANNA_SHOPAHOLIC = _prompt(shopaholic, "SHOPAHOLIC", dislikes.ANNA_SHOPAHOLIC_DISLIKES)
ANNA_EPERSONA = _prompt(
    epersona,
    "EPERSONA",
    dislikes.ANNA_EPERSONA_DISLIKES,
    voiceprint_prefix="EGIRL",
)


__all__ = [
    "ANNA_BOOMER",
    "ANNA_DELULU",
    "ANNA_EPERSONA",
    "ANNA_EX",
    "ANNA_FLIRTY",
    "ANNA_FOODIE",
    "ANNA_HONEST",
    "ANNA_KPOP",
    "ANNA_RELIGIOUS",
    "ANNA_SAVAGE",
    "ANNA_SHOPAHOLIC",
    "ANNA_SPIRITUAL",
    "ANNA_WARM",
    "ANNA_ZOOMER",
]
