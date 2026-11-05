"""Conversation session dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConversationSession:
    """Track state for a multi-turn conversation session.

    Attributes:
        session_id: Client-side label printed in the test header.
        gender: Gender of the selected prompt profile.
        personality: Personality of the selected prompt profile.
        prompt: Prompt text selected for that profile.
        sampling: Overrides sent with the start frame and each turn.

    """

    session_id: str
    gender: str
    personality: str
    prompt: str
    sampling: dict[str, float | int | bool] | None = None


__all__ = ["ConversationSession"]
