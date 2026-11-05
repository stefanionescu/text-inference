"""Unit tests for stream history commit behavior."""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
from dataclasses import dataclass

import pytest
from fastapi import WebSocketDisconnect

from src.execution.turn import StreamResponseRequest, stream_response
from tests.suites.unit.builders import RecordingWebSocket, typed_websocket, build_session_state, build_session_runtime
from tests.harness.environment.tokenizer import build_local_tokenizer

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from src.session.state import SessionState
    from src.session.runtime import SessionRuntime

SECOND_SEND = 2
USER_TEXT = "hello can you help me plan a trip"


@dataclass
class _DisconnectSecondSendWS:
    _send_count: int = 0

    async def send_text(self, _text: str) -> None:
        """Test send text."""
        self._send_count += 1
        if self._send_count >= SECOND_SEND:
            raise WebSocketDisconnect


def _start_session() -> tuple[SessionRuntime, SessionState]:
    """Return a runtime with limits out of the way and the initialized state of a new connection."""
    session_runtime = build_session_runtime(build_local_tokenizer())
    return session_runtime, build_session_state(session_runtime)


def _run_stream(
    session_runtime: SessionRuntime,
    state: SessionState,
    stream: AsyncIterator[str],
    *,
    websocket: object | None = None,
    user_utterance: str = USER_TEXT,
    history_user_utterance: str = USER_TEXT,
) -> str:
    """Stream one response to a recording socket unless the test supplies its own."""
    return asyncio.run(
        stream_response(
            StreamResponseRequest(
                websocket=typed_websocket(websocket or RecordingWebSocket()),
                stream=stream,
                connection_state=state,
                user_utterance=user_utterance,
                history_user_utterance=history_user_utterance,
                session_runtime=session_runtime,
            ),
        ),
    )


async def _empty_stream() -> AsyncIterator[str]:
    chunks: tuple[str, ...] = ()
    for chunk in chunks:
        yield chunk


async def _error_stream() -> AsyncIterator[str]:
    chunks: tuple[str, ...] = ()
    for chunk in chunks:
        yield chunk
    message = "boom"
    raise RuntimeError(message)


async def _two_chunk_stream() -> AsyncIterator[str]:
    chunks = ("alpha", "beta")
    for chunk in chunks:
        yield chunk


def test_stream_empty_history() -> None:
    """Test stream response skips history for empty output."""
    session_runtime, state = _start_session()

    out = _run_stream(session_runtime, state, _empty_stream())

    assert out == ""
    assert state.history_messages == []


def test_stream_error_history() -> None:
    """Test stream response skips history for error before visible text."""
    session_runtime, state = _start_session()

    with pytest.raises(RuntimeError, match="boom"):
        _run_stream(session_runtime, state, _error_stream())

    assert state.history_messages == []


def test_stream_disconnect_history() -> None:
    """Test stream response commits partial history after disconnect with visible text."""
    session_runtime, state = _start_session()

    out = _run_stream(session_runtime, state, _two_chunk_stream(), websocket=_DisconnectSecondSendWS())

    assert out == "alpha"
    assert state.history_messages is not None
    assert [(message.role, message.content) for message in state.history_messages] == [
        ("user", USER_TEXT),
        ("assistant", "alpha"),
    ]


def test_stream_empty_user() -> None:
    """Test stream response skips commit when history user is empty."""
    session_runtime, state = _start_session()

    out = _run_stream(session_runtime, state, _two_chunk_stream(), user_utterance="", history_user_utterance="")

    assert out == "alphabeta"
    assert state.history_messages == []


def test_stream_history_user() -> None:
    """Test stream response persists supplied history user utterance verbatim."""
    session_runtime, state = _start_session()

    out = _run_stream(
        session_runtime,
        state,
        _two_chunk_stream(),
        user_utterance="short user text",
        history_user_utterance="expanded user text for committed history",
    )

    assert out == "alphabeta"
    assert state.history_messages is not None
    assert [(message.role, message.content) for message in state.history_messages] == [
        ("user", "expanded user text for committed history"),
        ("assistant", "alphabeta"),
    ]
