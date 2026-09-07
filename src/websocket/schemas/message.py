"""Message-turn schema for WebSocket clients."""

from __future__ import annotations

from typing import Literal
from .versioned import VersionedMessage


class TurnMessage(VersionedMessage):
    """Strict schema for message turn payloads."""

    type: Literal["message"]
    user_utterance: str | None = None
    sampling: dict[str, object] | None = None
    temperature: object | None = None
    top_p: object | None = None
    top_k: object | None = None
    min_p: object | None = None
    repetition_penalty: object | None = None
    presence_penalty: object | None = None
    frequency_penalty: object | None = None
    sanitize_output: object | None = None


__all__ = ["TurnMessage"]
