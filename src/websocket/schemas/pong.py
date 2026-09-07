"""Pong message schema for WebSocket clients."""

from __future__ import annotations

from typing import Literal
from .versioned import VersionedMessage


class PongMessage(VersionedMessage):
    """Strict schema for pong payloads."""

    type: Literal["pong"]


__all__ = ["PongMessage"]
