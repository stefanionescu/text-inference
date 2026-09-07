"""End message schema for WebSocket clients."""

from __future__ import annotations

from typing import Literal
from .versioned import VersionedMessage


class EndMessage(VersionedMessage):
    """Strict schema for end payloads."""

    type: Literal["end"]


__all__ = ["EndMessage"]
