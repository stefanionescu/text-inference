"""Engine-related dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class EngineOutput:
    """Unified output format for streaming generation."""

    text: str
    token_ids: list[int] | None = None
    is_finished: bool = False


__all__ = ["EngineOutput"]
