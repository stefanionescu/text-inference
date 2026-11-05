"""Strict schemas for the WebSocket message contract."""

from __future__ import annotations

from typing import Literal

from pydantic import Field, BaseModel, ConfigDict, field_validator


class VersionedMessage(BaseModel):
    """Base client message that enforces protocol version and strict fields.

    Attributes:
        model_config: Pydantic configuration that rejects unknown frame fields.
        v: Protocol version of the frame.

    """

    model_config = ConfigDict(extra="forbid")
    v: int


class HistoryItem(BaseModel):
    """One history message item in start payloads.

    Attributes:
        model_config: Pydantic configuration that rejects unknown item fields.
        role: Chat role, either `user` or `assistant`.
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
            value: Raw role value.

        Returns:
            The role as stripped lowercase text.

        """
        return str(value).strip().lower()

    @field_validator("role")
    @staticmethod
    def _validate_role(value: str) -> str:
        """Reject unsupported history roles.

        Args:
            value: Normalized role.

        Returns:
            The role unchanged.

        Raises:
            ValueError: The role is not `user` or `assistant`.

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
        temperature: Client override for temperature.
        top_p: Client override for top-P.
        top_k: Client override for top-K.
        min_p: Client override for minimum token probability.
        repetition_penalty: Client override for the repetition penalty.
        presence_penalty: Client override for the presence penalty.
        frequency_penalty: Client override for the frequency penalty.
        sanitize_output: Client choice to sanitize streamed text, which must be a bool.

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
        type: Frame tag, always `start`.
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        history: Seed conversation history; an explicit null becomes an empty list.
        prompt: Start prompt text.
        sampling: Nested sampling overrides, which win over the top-level fields.

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
            value: Raw `history` field.

        Returns:
            An empty list for None, otherwise the value unchanged.

        """
        if value is None:
            return []
        return value


class TurnMessage(_SamplingOverrideMessage):
    """Strict schema for message turn payloads.

    Attributes:
        type: Frame tag, always `message`.
        user_utterance: Text of the follow-up user turn.
        sampling: Nested overrides for this turn, which win over the top-level fields.

    """

    type: Literal["message"]
    user_utterance: str | None = None
    sampling: dict[str, object] | None = None


class CancelMessage(VersionedMessage):
    """Strict schema for cancel payloads.

    Attributes:
        type: Frame tag, always `cancel`.

    """

    type: Literal["cancel"]


class EndMessage(VersionedMessage):
    """Strict schema for end payloads.

    Attributes:
        type: Frame tag, always `end`.

    """

    type: Literal["end"]


class PingMessage(VersionedMessage):
    """Strict schema for ping payloads.

    Attributes:
        type: Frame tag, always `ping`.

    """

    type: Literal["ping"]


class PongMessage(VersionedMessage):
    """Strict schema for pong payloads.

    Attributes:
        type: Frame tag, always `pong`.

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
