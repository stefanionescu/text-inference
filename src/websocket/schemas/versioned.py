"""Base schema for versioned WebSocket client messages."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class VersionedMessage(BaseModel):
    """Base client message that enforces protocol version and strict fields."""

    model_config = ConfigDict(extra="forbid")
    v: int


__all__ = ["VersionedMessage"]
