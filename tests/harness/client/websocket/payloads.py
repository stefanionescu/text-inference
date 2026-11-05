"""Shared WebSocket message payload builders.

This module provides canonical payload builders for WebSocket test messages.
All messages use the flat format (no envelope wrapper).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from config.runtime.websocket import WEBSOCKET_PROTOCOL_VERSION

if TYPE_CHECKING:
    from tests.state.metrics import SessionContext


def build_cancel_payload() -> dict[str, Any]:
    """Build a cancel message."""
    return {"type": "cancel", "v": WEBSOCKET_PROTOCOL_VERSION}


def build_end_payload() -> dict[str, Any]:
    """Build an end message."""
    return {"type": "end", "v": WEBSOCKET_PROTOCOL_VERSION}


def build_message_payload(
    user_text: str,
    *,
    sampling: dict[str, float | int | bool] | None = None,
) -> dict[str, Any]:
    """Build a message payload for subsequent conversation turns.

    Args:
        user_text: The user's message text.
        sampling: Optional sampling parameter overrides.

    Returns:
        A dict ready to be JSON-serialized and sent over WebSocket.

    """
    message: dict[str, Any] = {"type": "message", "v": WEBSOCKET_PROTOCOL_VERSION, "user_utterance": user_text}
    if sampling:
        message["sampling"] = sampling
    return message


def build_start_payload(
    context: SessionContext,
    *,
    history: list[dict[str, str]] | None = None,
) -> dict[str, Any]:
    """Build the bootstrap-only start message payload.

    Args:
        context: Session context with optional start fields.
        history: Conversation history as [{role, content}, ...] (default empty).

    Returns:
        A dict ready to be JSON-serialized and sent over WebSocket.

    """
    message: dict[str, Any] = {
        "type": "start",
        "v": WEBSOCKET_PROTOCOL_VERSION,
        "history": history if history is not None else [],
    }
    if context.gender is not None:
        message["gender"] = context.gender
    if context.personality is not None:
        message["personality"] = context.personality
    if context.prompt is not None:
        message["prompt"] = context.prompt
    if context.sampling is not None:
        message["sampling"] = context.sampling
    return message


__all__ = [
    "build_cancel_payload",
    "build_end_payload",
    "build_message_payload",
    "build_start_payload",
]
