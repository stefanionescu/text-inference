"""Unit tests for stream history commit behavior."""

from __future__ import annotations
import pytest
import asyncio
from typing import TYPE_CHECKING, cast
from fastapi import WebSocketDisconnect
from src.session.state import SessionState
from src.runtime.config import HistorySettings
from src.session.runtime import SessionRuntime
from dataclasses import replace, dataclass, field
from src.execution.turn import StreamResponseRequest, stream_response
from tests.harness.environment.tokenizer import build_local_tokenizer
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS

if TYPE_CHECKING:
    from fastapi import WebSocket
    from collections.abc import AsyncIterator

SECOND_SEND = 2


@dataclass
class _NoopWebSocket:
    sent: list[str] = field(default_factory=list)

    async def send_text(self, text: str) -> None:
        """Test send text."""
        self.sent.append(text)


@dataclass
class _DisconnectSecondSendWS:
    _send_count: int = 0

    async def send_text(self, _text: str) -> None:
        """Test send text."""
        self._send_count += 1
        if self._send_count >= SECOND_SEND:
            raise WebSocketDisconnect


def _build_session() -> SessionRuntime:
    return SessionRuntime(
        tokenizer=build_local_tokenizer(),
        settings=replace(
            DEFAULT_APPLICATION_SETTINGS,
            history=HistorySettings(
                trigger_tokens=1000,
                target_tokens=800,
            ),
        ),
    )


async def _empty_stream() -> AsyncIterator[str]:
    chunks: tuple[str, ...] = ()
    for chunk in chunks:
        yield chunk


async def _error_stream() -> AsyncIterator[str]:
    message = "boom"
    raise RuntimeError(message)
    yield ""


async def _two_chunk_stream() -> AsyncIterator[str]:
    chunks = ("alpha", "beta")
    for chunk in chunks:
        yield chunk


def test_stream_empty_history() -> None:
    """Test stream response skips history for empty output."""
    session_runtime = _build_session()
    state = SessionState(meta={})
    session_runtime.initialize_session(state)

    out = asyncio.run(
        stream_response(
            StreamResponseRequest(
                websocket=cast("WebSocket", _NoopWebSocket()),
                stream=_empty_stream(),
                connection_state=state,
                user_utterance="hello can you help me plan a trip",
                history_user_utterance="hello can you help me plan a trip",
                session_runtime=session_runtime,
            ),
        ),
    )

    assert out == ""
    assert state.history_messages == []


def test_stream_error_history() -> None:
    """Test stream response skips history for error before visible text."""
    session_runtime = _build_session()
    state = SessionState(meta={})
    session_runtime.initialize_session(state)

    with pytest.raises(RuntimeError, match="boom"):
        asyncio.run(
            stream_response(
                StreamResponseRequest(
                    websocket=cast("WebSocket", _NoopWebSocket()),
                    stream=_error_stream(),
                    connection_state=state,
                    user_utterance="hello can you help me plan a trip",
                    history_user_utterance="hello can you help me plan a trip",
                    session_runtime=session_runtime,
                ),
            ),
        )

    assert state.history_messages == []


def test_stream_disconnect_history() -> None:
    """Test stream response commits partial history after disconnect with visible text."""
    session_runtime = _build_session()
    state = SessionState(meta={})
    session_runtime.initialize_session(state)

    out = asyncio.run(
        stream_response(
            StreamResponseRequest(
                websocket=cast("WebSocket", _DisconnectSecondSendWS()),
                stream=_two_chunk_stream(),
                connection_state=state,
                user_utterance="hello can you help me plan a trip",
                history_user_utterance="hello can you help me plan a trip",
                session_runtime=session_runtime,
            ),
        ),
    )

    assert out == "alpha"
    assert state.history_messages is not None
    assert [(message.role, message.content) for message in state.history_messages] == [
        ("user", "hello can you help me plan a trip"),
        ("assistant", "alpha"),
    ]


def test_stream_empty_user() -> None:
    """Test stream response skips commit when history user is empty."""
    session_runtime = _build_session()
    state = SessionState(meta={})
    session_runtime.initialize_session(state)

    out = asyncio.run(
        stream_response(
            StreamResponseRequest(
                websocket=cast("WebSocket", _NoopWebSocket()),
                stream=_two_chunk_stream(),
                connection_state=state,
                user_utterance="",
                history_user_utterance="",
                session_runtime=session_runtime,
            ),
        ),
    )

    assert out == "alphabeta"
    assert state.history_messages == []


def test_stream_history_user() -> None:
    """Test stream response persists supplied history user utterance verbatim."""
    session_runtime = _build_session()
    state = SessionState(meta={})
    session_runtime.initialize_session(state)

    out = asyncio.run(
        stream_response(
            StreamResponseRequest(
                websocket=cast("WebSocket", _NoopWebSocket()),
                stream=_two_chunk_stream(),
                connection_state=state,
                user_utterance="short user text",
                history_user_utterance="expanded user text for committed history",
                session_runtime=session_runtime,
            ),
        ),
    )

    assert out == "alphabeta"
    assert state.history_messages is not None
    assert [(message.role, message.content) for message in state.history_messages] == [
        ("user", "expanded user text for committed history"),
        ("assistant", "alphabeta"),
    ]
