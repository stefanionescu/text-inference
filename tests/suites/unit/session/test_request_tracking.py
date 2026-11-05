"""Unit tests for session request tracking utilities."""

from __future__ import annotations

from typing import cast
import asyncio
from unittest.mock import Mock, AsyncMock

import pytest

from src.session.state import SessionState
from src.session.requests import (
    is_request_cancelled,
    abort_session_requests,
    cancel_session_requests,
    cleanup_session_requests,
)


def _make_state(
    *,
    active_request_task: asyncio.Task[object] | None = None,
    active_request_id: str | None = None,
    is_cancel_requested: bool = False,
) -> SessionState:
    """Build explicitly typed session state for request-tracking tests.

    Args:
        active_request_task: Task that runs the active request.
        active_request_id: ID of the active request.
        is_cancel_requested: Whether cancel is requested.

    Returns:
        Explicitly typed session state for request-tracking tests.

    """
    return SessionState(
        meta={},
        active_request_task=active_request_task,
        active_request_id=active_request_id,
        is_cancel_requested=is_cancel_requested,
    )


def test_request_cancel_states() -> None:
    """Test cancellation state matching."""
    if is_request_cancelled(None, "req1") is not True:
        pytest.fail("Assertion failed")
    state = _make_state(active_request_id="req1", is_cancel_requested=True)
    if is_request_cancelled(state, "req1") is not True:
        pytest.fail("Assertion failed")
    state = _make_state(active_request_id=None)
    if is_request_cancelled(state, "req1") is not False:
        pytest.fail("Assertion failed")
    state = _make_state(active_request_id="req1")
    if is_request_cancelled(state, "req1") is not False:
        pytest.fail("Assertion failed")
    state = _make_state(active_request_id="req2")
    if is_request_cancelled(state, "req1") is not True:
        pytest.fail("Assertion failed")


def test_cleanup_request_states() -> None:
    """Test cleanup extracts active ids and clears tasks."""
    result = cleanup_session_requests(None)
    assert result == {"active": ""}
    state = _make_state(active_request_id="a1")
    result = cleanup_session_requests(state)
    assert result == {"active": "a1"}
    if state.active_request_id is not None:
        pytest.fail("Assertion failed")
    task = Mock(spec=asyncio.Task)
    state = _make_state(active_request_id="a1", active_request_task=cast("asyncio.Task[object]", task))
    result = cleanup_session_requests(state)
    assert result == {"active": "a1"}
    if state.active_request_task is not None:
        pytest.fail("Assertion failed")


# --- cancel_session_requests ---


def test_cancel_marks_requested() -> None:
    """Test cancel marks cancel requested."""
    state = _make_state(active_request_id="r1")
    cancel_session_requests(state)
    if state.is_cancel_requested is not True:
        pytest.fail("Assertion failed")


def test_cancel_stops_task() -> None:
    """Test cancel cancels running task."""
    task = Mock(spec=asyncio.Task)
    task.done.return_value = False
    state = _make_state(active_request_task=cast("asyncio.Task[object]", task))
    cancel_session_requests(state)
    task.cancel.assert_called_once_with()


def test_abort_active_request() -> None:
    """Test abort session requests aborts engine with active id."""
    engine = AsyncMock()
    state = _make_state(active_request_id="req-123")

    asyncio.run(abort_session_requests(state, engine))

    engine.abort.assert_awaited_once_with("req-123")
    if state.active_request_id is not None:
        pytest.fail("Assertion failed")
