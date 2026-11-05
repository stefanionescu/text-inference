"""Strict schemas for the WebSocket message contract."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, BaseModel, ConfigDict, field_validator


class VersionedMessage(BaseModel):
    """Base client message that enforces protocol version and strict fields.

    Attributes:
        model_config: Model config.
        v: Protocol version of the frame.

    """

    model_config = ConfigDict(extra="forbid")
    v: int


class HistoryItem(BaseModel):
    """One history message item in start payloads.

    Attributes:
        model_config: Model config.
        role: Chat role of the message.
        content: Text content of the message.

    """

    model_config = ConfigDict(extra="forbid")
    role: str
    content: str

    @field_validator("role", mode="before")
    @staticmethod
    def _normalize_role(value: object) -> str:
        """Normalize history role values before validation.

        Args:
            value: Value to check or convert.

        Returns:
            The updated text.

        """
        return str(value).strip().lower()

    @field_validator("role")
    @staticmethod
    def _validate_role(value: str) -> str:
        """Reject unsupported history roles.

        Args:
            value: Value to check or convert.

        Returns:
            The resulting text.

        Raises:
            ValueError: History role must be 'user' or 'assistant'.

        """
        if value not in {"user", "assistant"}:
            message = "history role must be 'user' or 'assistant'"
            raise ValueError(message)
        return value


class _SamplingOverrideMessage(VersionedMessage):
    """Top-level sampling overrides, typed loosely so `extract_sampling_overrides` reports bad values.

    Each subclass declares `sampling` itself, because it is the only override
    Pydantic can reject and the parser reports the first failing field in order.

    Attributes:
        temperature: Sampling temperature.
        top_p: Top-P sampling value.
        top_k: Top-K sampling value.
        min_p: Minimum-probability sampling value.
        repetition_penalty: Repetition penalty.
        presence_penalty: Presence penalty.
        frequency_penalty: Frequency penalty.
        sanitize_output: Sanitize output.

    """

    temperature: object | None = None
    top_p: object | None = None
    top_k: object | None = None
    min_p: object | None = None
    repetition_penalty: object | None = None
    presence_penalty: object | None = None
    frequency_penalty: object | None = None
    sanitize_output: object | None = None


class StartMessage(_SamplingOverrideMessage):
    """Strict schema for start messages.

    Attributes:
        type: Message type.
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        history: Conversation history to use.
        prompt: Prompt text.
        sampling: Sampling overrides of the request.

    """

    type: Literal["start"]
    gender: str | None = None
    personality: str | None = None
    history: list[HistoryItem] = Field(default_factory=list)
    prompt: str | None = None
    sampling: dict[str, object] | None = None

    @field_validator("history", mode="before")
    @staticmethod
    def _validate_history_items(value: object) -> object:
        """Treat omitted history and explicit null as empty history.

        Args:
            value: Value to check or convert.

        Returns:
            The object.

        """
        if value is None:
            return []
        return value


class TurnMessage(_SamplingOverrideMessage):
    """Strict schema for message turn payloads.

    Attributes:
        type: Message type.
        user_utterance: User utterance.
        sampling: Sampling overrides of the request.

    """

    type: Literal["message"]
    user_utterance: str | None = None
    sampling: dict[str, object] | None = None


class CancelMessage(VersionedMessage):
    """Strict schema for cancel payloads.

    Attributes:
        type: Message type.

    """

    type: Literal["cancel"]


class EndMessage(VersionedMessage):
    """Strict schema for end payloads.

    Attributes:
        type: Message type.

    """

    type: Literal["end"]


class PingMessage(VersionedMessage):
    """Strict schema for ping payloads.

    Attributes:
        type: Message type.

    """

    type: Literal["ping"]


class PongMessage(VersionedMessage):
    """Strict schema for pong payloads.

    Attributes:
        type: Message type.

    """

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
