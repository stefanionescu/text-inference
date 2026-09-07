"""Ping message schema for WebSocket clients."""

from __future__ import annotations

from typing import Literal
from .versioned import VersionedMessage


class PingMessage(VersionedMessage):
    """Strict schema for ping payloads."""

    type: Literal["ping"]


__all__ = ["PingMessage"]
