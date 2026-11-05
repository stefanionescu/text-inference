"""Strict schemas for the WebSocket message contract."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, BaseModel, ConfigDict, field_validator


class VersionedMessage(BaseModel):
    """Base client message that enforces protocol version and strict fields."""

    model_config = ConfigDict(extra="forbid")
    v: int


class HistoryItem(BaseModel):
    """One history message item in start payloads."""

    model_config = ConfigDict(extra="forbid")
    role: str
    content: str

    @field_validator("role", mode="before")
    @staticmethod
    def _normalize_role(value: object) -> str:
        """Normalize history role values before validation."""
        return str(value).strip().lower()

    @field_validator("role")
    @staticmethod
    def _validate_role(value: str) -> str:
        """Reject unsupported history roles."""
        if value not in {"user", "assistant"}:
            message = "history role must be 'user' or 'assistant'"
            raise ValueError(message)
        return value


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
        """Treat omitted history and explicit null as empty history."""
        if value is None:
            return []
        return value


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


class CancelMessage(VersionedMessage):
    """Strict schema for cancel payloads."""

    type: Literal["cancel"]


class EndMessage(VersionedMessage):
    """Strict schema for end payloads."""

    type: Literal["end"]


class PingMessage(VersionedMessage):
    """Strict schema for ping payloads."""

    type: Literal["ping"]


class PongMessage(VersionedMessage):
    """Strict schema for pong payloads."""

    type: Literal["pong"]


__all__ = [
    "CancelMessage",
    "EndMessage",
    "HistoryItem",
    "PingMessage",
    "PongMessage",
    "StartMessage",
    "TurnMessage",
    "VersionedMessage",
]
