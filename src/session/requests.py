"""Request and task tracking for session management.

This module handles the tracking of active requests and asyncio tasks:

1. Request ID Tracking:
   - active_request_id: The current generation request
   - is_cancel_requested: Cooperative cancellation flag for in-flight streams

2. Task Management:
   - has_running_task: Check if a session has active work

3. Cancellation:
   - is_request_cancelled: Check if a request was superseded
   - cancel_session_requests: Mark session as cancelled
   - cleanup_session_requests: Extract and clear request IDs

These utilities support clean cancellation of in-flight generation
and proper cleanup when connections close.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
import contextlib

if TYPE_CHECKING:
    from collections.abc import Callable, Awaitable

    from src.session.state import SessionState
    from src.engines.protocol import Engine


async def _run_request(
    state: SessionState,
    request_id: str,
    operation: Callable[[], Awaitable[None]],
) -> None:
    """Release matching request state when its task finishes."""
    try:
        await operation()
    finally:
        async with state.request_lock:
            if state.lifecycle_state != "cancelling":
                cleanup_session_requests(state, request_id=request_id)


def is_request_cancelled(state: SessionState | None, request_id: str) -> bool:
    """Check if a request has been cancelled or superseded.

    A request is considered cancelled if:
    - The session doesn't exist
    - The session has is_cancel_requested=True
    - The session's active_request_id differs from the given request_id
    """
    if not state:
        return True
    if state.lifecycle_state in {"cancelling", "closed"} or state.is_cancel_requested:
        return True
    active = state.active_request_id
    return bool(active and active != request_id)


def has_running_task(state: SessionState | None) -> bool:
    """Check if the session has a running task."""
    if state is None:
        return False
    task = state.active_request_task
    if task is None:
        return False
    return not task.done()


def begin_session_request(state: SessionState, request_id: str) -> bool:
    """Start tracking a new active request.

    Returns:
        False when the session is already closed; otherwise True.

    """
    if state.lifecycle_state == "closed":
        return False
    state.active_request_id = request_id
    state.is_cancel_requested = False
    state.lifecycle_state = "running"
    return True


def attach_request_task(
    state: SessionState,
    *,
    request_id: str,
    task: asyncio.Task[object],
) -> None:
    """Attach a task handle to the matching active request only."""
    if state.lifecycle_state == "closed":
        return
    if state.active_request_id != request_id:
        return
    state.active_request_task = task


def cancel_session_requests(state: SessionState) -> None:
    """Mark the session as cancelled and cancel any running task.

    Sets is_cancel_requested so any in-flight generation knows to stop yielding
    tokens.
    """
    state.lifecycle_state = "cancelling"
    state.is_cancel_requested = True
    task = state.active_request_task
    if task and not task.done():
        task.cancel()


def cleanup_session_requests(
    state: SessionState | None,
    *,
    request_id: str | None = None,
    is_forced: bool = False,
) -> dict[str, str]:
    """Extract and clear request IDs from the session.

    By default, cleanup only applies when request_id matches the current
    active request. This prevents stale background tasks from clearing newer
    request state.
    """
    if not state:
        return {"active": ""}
    if not is_forced and request_id is not None and state.active_request_id != request_id:
        return {"active": state.active_request_id or ""}
    cleared_request_id = state.active_request_id or ""
    state.active_request_id = None
    state.active_request_task = None
    if state.lifecycle_state != "closed":
        state.lifecycle_state = "idle"
    state.is_cancel_requested = False
    return {"active": cleared_request_id}


def close_session_requests(state: SessionState) -> None:
    """Mark the session closed and clear all active request pointers."""
    state.lifecycle_state = "closed"
    state.is_cancel_requested = True
    state.active_request_id = None
    state.active_request_task = None


async def spawn_session_task(
    state: SessionState,
    *,
    request_id: str,
    operation: Callable[[], Awaitable[None]],
) -> asyncio.Task[None] | None:
    """Atomically create and attach a supervised session request."""
    async with state.request_lock:
        if state.lifecycle_state != "idle" or has_running_task(state):
            return None
        begin_session_request(state, request_id)
        task = asyncio.create_task(
            _run_request(state, request_id, operation),
        )
        attach_request_task(state, request_id=request_id, task=task)
        return task


async def abort_session_requests(state: SessionState | None, engine: Engine) -> None:
    """Cancel and await active work, then clear only the captured request."""
    if state is None:
        return
    async with state.request_lock:
        request_id = state.active_request_id
        task = state.active_request_task
        cancel_session_requests(state)
    try:
        if request_id:
            await engine.abort(request_id)
    finally:
        if task is not None:
            with contextlib.suppress(asyncio.CancelledError):
                await task
        async with state.request_lock:
            cleanup_session_requests(state, request_id=request_id)


__all__ = [
    "abort_session_requests",
    "attach_request_task",
    "begin_session_request",
    "cancel_session_requests",
    "cleanup_session_requests",
    "close_session_requests",
    "has_running_task",
    "is_request_cancelled",
    "spawn_session_task",
]
