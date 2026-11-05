"""Conversation session dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConversationSession:
    """Track state for a multi-turn conversation session.

    Attributes:
        session_id: ID of the session.
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        prompt: Prompt text.
        sampling: Sampling overrides of the request.

    """

    session_id: str
    gender: str
    personality: str
    prompt: str
    sampling: dict[str, float | int | bool] | None = None


__all__ = ["ConversationSession"]
