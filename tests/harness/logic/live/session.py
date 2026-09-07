"""Live session payload builders.

This module keeps payload construction in the logic layer so `tests.state`
remains a pure dataclass package without websocket helper dependencies.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from tests.state.metrics import SessionContext
from tests.harness.client.websocket.payloads import (
    build_message_payload as build_websocket_message_payload,
)
from tests.harness.client.websocket.payloads import (
    build_start_payload as build_websocket_start_payload,
)

if TYPE_CHECKING:
    from tests.state.live import LiveSession


def build_start_payload(session: LiveSession) -> dict[str, Any]:
    """Build the bootstrap-only start payload for a live session turn."""
    context = SessionContext(
        session_id=session.session_id,
        gender=session.profile.gender,
        personality=session.profile.personality,
        prompt=session.profile.prompt,
        sampling=session.sampling,
    )
    return build_websocket_start_payload(context, history=session.history)


def build_message_payload(session: LiveSession, user_text: str) -> dict[str, Any]:
    """Build the message payload for subsequent live session turns."""
    return build_websocket_message_payload(
        user_text,
        sampling=session.sampling,
    )


__all__ = ["build_message_payload", "build_start_payload"]
