"""Conversation session dataclasses."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ConversationSession:
    """Track state for a multi-turn conversation session."""

    session_id: str
    gender: str
    personality: str
    prompt: str
    sampling: dict[str, float | int | bool] | None = None


__all__ = ["ConversationSession"]
