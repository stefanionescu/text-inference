"""Start message schema for WebSocket clients."""

from __future__ import annotations

from .history import HistoryItem
from typing import Literal, cast
from .versioned import VersionedMessage
from pydantic import Field, field_validator


class StartMessage(VersionedMessage):
    """Strict schema for start messages."""

    type: Literal["start"]
    gender: str | None = None
    personality: str | None = None
    history: list[HistoryItem] = Field(default_factory=list)
    prompt: str | None = None
    sampling: dict[str, object] | None = None
    temperature: object | None = None
    top_p: object | None = None
    top_k: object | None = None
    min_p: object | None = None
    repetition_penalty: object | None = None
    presence_penalty: object | None = None
    frequency_penalty: object | None = None
    sanitize_output: object | None = None

    @field_validator("history", mode="before")
    @staticmethod
    def _validate_history_items(value: object) -> object:
        """Validate history items through the dedicated item schema."""
        if value is None:
            return []
        if not isinstance(value, list):
            return value
        items = cast("list[object]", value)
        return [HistoryItem.model_validate(item) for item in items]


__all__ = ["StartMessage"]
