"""History item schema for WebSocket start messages."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, field_validator


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


__all__ = ["HistoryItem"]
