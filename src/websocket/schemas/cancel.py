"""Cancel message schema for WebSocket clients."""

from __future__ import annotations

from typing import Literal
from .versioned import VersionedMessage


class CancelMessage(VersionedMessage):
    """Strict schema for cancel payloads."""

    type: Literal["cancel"]


__all__ = ["CancelMessage"]
