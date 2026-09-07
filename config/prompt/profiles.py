"""Gender and personality pairs used by deployment warmup."""

from __future__ import annotations

WARMUP_PROMPT_PAIRS: list[tuple[str, str]] = [
    ("female", "flirty"),
    ("male", "flirty"),
]

VALID_GENDERS: set[str] = {"female", "male"}

__all__ = ["VALID_GENDERS", "WARMUP_PROMPT_PAIRS"]
