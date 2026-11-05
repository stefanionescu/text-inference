"""Session-scoped dataclasses for per-connection state."""

from __future__ import annotations

import time
import uuid
from typing import Any, Literal
import asyncio
from dataclasses import field, dataclass


@dataclass
class HistoryMessage:
    """One stored history message."""

    role: Literal["user", "assistant"]
    content: str


@dataclass
class SessionState:
    """Container for all mutable session-scoped payload.

    This dataclass holds everything needed to manage a single user session,
    from conversation history to request tracking to rate limiting.
    Created per-connection; the connection IS the session identity.

    Attributes:
        meta: Extensible metadata dictionary containing session configuration.
        session_id: Stable server-generated ID for this websocket session.
        history_messages: Conversation history store.
        active_request_task: Reference to the currently running asyncio.Task
            for this session.
        active_request_id: Tracks the current generation request. Used
            to detect stale streaming responses when a newer request supersedes
            an older one. None when idle.
        lifecycle_state: Request lifecycle state for transition safety:
            'idle' | 'running' | 'cancelling' | 'closed'.
        is_cancel_requested: Cooperative cancellation flag for in-flight streams.
        request_lock: Lock guarding lifecycle/request mutation transitions.
        created_at: Monotonic timestamp when the session was first created.

    """

    meta: dict[str, Any]
    session_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    history_messages: list[HistoryMessage] | None = None
    active_request_task: asyncio.Task[object] | None = None
    active_request_id: str | None = None
    lifecycle_state: Literal["idle", "running", "cancelling", "closed"] = "idle"
    is_cancel_requested: bool = False
    request_lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    created_at: float = field(default_factory=time.monotonic)


__all__ = ["HistoryMessage", "SessionState"]
