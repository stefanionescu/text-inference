"""Unit tests for start/message planning flow."""

from __future__ import annotations
import json
import pytest
import asyncio
from dataclasses import replace
from unittest.mock import AsyncMock
from typing import TYPE_CHECKING, cast
from src.runtime.config import HistorySettings
from src.session.runtime import SessionRuntime
from src.messages.message import plan_message_turn
from src.messages.start import bootstrap_start_turn
from src.session.state import HistoryMessage, SessionState
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS
from tests.harness.environment.tokenizer import build_local_tokenizer, use_local_tokenizers
from tests.harness.messages.unit import ASSISTANT_FIRST_MESSAGES, ASSISTANT_FIRST_PAYLOAD, HISTORY_PAYLOAD, MESSAGES

if TYPE_CHECKING:
    from fastapi import WebSocket
    from src.tokens.tokenizer import ThreadSafeTokenizer


class _NoopWebSocket:
    def __init__(self) -> None:
        self.sent: list[str] = []
        self.is_closed = False
        self.close_code: int | None = None

    async def send_text(self, text: str) -> None:
        """Test send text."""
        sent = self.sent
        payload = text
        sent.append(payload)

    async def close(self, code: int = 1008) -> None:
        """Test close."""
        close_code = code
        self.is_closed = True
        self.close_code = close_code


def _build_session(
    *,
    trigger_tokens: int = 1000,
    target_tokens: int = 800,
    tokenizer: ThreadSafeTokenizer,
) -> SessionRuntime:
    AsyncMock()
    history_config = HistorySettings(
        trigger_tokens=trigger_tokens,
        target_tokens=target_tokens,
    )
    return SessionRuntime(
        tokenizer=tokenizer,
        settings=replace(DEFAULT_APPLICATION_SETTINGS, history=history_config),
    )


def _start_payload(history: list[dict[str, str]]) -> dict[str, object]:
    payload: dict[str, object] = {
        "gender": "female",
        "personality": "calm",
        "prompt": "Stay concise.",
    }
    payload["history"] = history
    return payload


def test_history_user_bootstrap() -> None:
    """Test bootstrap start imports user-first history."""
    with use_local_tokenizers() as tokenizer:
        session_runtime = _build_session(tokenizer=tokenizer)
        state = SessionState(meta={})
        websocket = _NoopWebSocket()

        is_successful = asyncio.run(
            bootstrap_start_turn(
                cast("WebSocket", websocket),
                _start_payload(HISTORY_PAYLOAD[:2]),
                state,
                session_runtime=session_runtime,
            ),
        )

        if is_successful is not True:
            pytest.fail("Assertion failed")
        if state.active_request_task is not None:
            pytest.fail("Assertion failed")
        assert state.history_messages == [MESSAGES[0], MESSAGES[1]]
        assert json.loads(websocket.sent[-1]) == {"type": "done", "status": 200}


def test_history_assistant_bootstrap() -> None:
    """Test bootstrap start imports assistant-first history."""
    with use_local_tokenizers() as tokenizer:
        session_runtime = _build_session(tokenizer=tokenizer)
        state = SessionState(meta={})
        websocket = _NoopWebSocket()

        is_successful = asyncio.run(
            bootstrap_start_turn(
                cast("WebSocket", websocket),
                _start_payload(ASSISTANT_FIRST_PAYLOAD[:4]),
                state,
                session_runtime=session_runtime,
            ),
        )

        if is_successful is not True:
            pytest.fail("Assertion failed")
        assert state.history_messages == ASSISTANT_FIRST_MESSAGES[:4]
        assert json.loads(websocket.sent[-1]) == {"type": "done", "status": 200}


def test_history_payload_rejection() -> None:
    """Test bootstrap start rejects invalid history payload."""
    with use_local_tokenizers() as tokenizer:
        session_runtime = _build_session(tokenizer=tokenizer)
        state = SessionState(meta={})
        websocket = _NoopWebSocket()

        is_successful = asyncio.run(
            bootstrap_start_turn(
                cast("WebSocket", websocket),
                {"history": HISTORY_PAYLOAD[:2]},
                state,
                session_runtime=session_runtime,
            ),
        )

        if is_successful is not False:
            pytest.fail("Assertion failed")
        if websocket.is_closed is not True:
            pytest.fail("Assertion failed")
        assert any("invalid_payload" in payload for payload in websocket.sent)


def test_plan_committed_history() -> None:
    """Test message planning uses the session's committed history."""
    session_runtime = _build_session(tokenizer=build_local_tokenizer())
    state = SessionState(meta={"prompt": "Stay concise."})
    session_runtime.initialize_session(state)
    state.meta["prompt"] = "Stay concise."
    state.history_messages = [
        HistoryMessage(role="user", content="hello can you help me plan a trip"),
        HistoryMessage(role="assistant", content="sure tell me your budget"),
    ]

    plan = asyncio.run(
        plan_message_turn(
            cast("WebSocket", _NoopWebSocket()),
            {"user_utterance": "three"},
            state,
            session_runtime=session_runtime,
        ),
    )

    assert plan is not None
    assert plan.user_utterance == "three"
    assert state.history_messages is not None
    assert [(message.role, message.content) for message in state.history_messages] == [
        ("user", "hello can you help me plan a trip"),
        ("assistant", "sure tell me your budget"),
    ]
    assert [(message.role, message.content) for message in plan.history_messages] == [
        ("user", "hello can you help me plan a trip"),
        ("assistant", "sure tell me your budget"),
    ]


def test_plan_rejects_empty() -> None:
    """Test plan message turn rejects empty user utterance."""
    session_runtime = _build_session(tokenizer=build_local_tokenizer())
    state = SessionState(meta={})
    session_runtime.initialize_session(state)
    websocket = _NoopWebSocket()

    plan = asyncio.run(
        plan_message_turn(
            cast("WebSocket", websocket),
            {"user_utterance": "  "},
            state,
            session_runtime=session_runtime,
        ),
    )

    if plan is not None:
        pytest.fail("Assertion failed")
    assert any("user_utterance is required" in payload for payload in websocket.sent)
