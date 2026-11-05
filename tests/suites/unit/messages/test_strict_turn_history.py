"""Unit tests for start/message planning flow."""

from __future__ import annotations

import json
import asyncio

import pytest

from src.session.state import SessionState, HistoryMessage
from src.messages.start import bootstrap_start_turn
from src.messages.message import plan_message_turn
from tests.suites.unit.builders import RecordingWebSocket, typed_websocket, build_session_state, build_session_runtime
from tests.harness.messages.unit import MESSAGES, HISTORY_PAYLOAD, ASSISTANT_FIRST_PAYLOAD, ASSISTANT_FIRST_MESSAGES
from tests.harness.environment.tokenizer import use_local_tokenizers, build_local_tokenizer


def _start_payload(history: list[dict[str, str]]) -> dict[str, object]:
    payload: dict[str, object] = {
        "gender": "female",
        "personality": "calm",
        "prompt": "Stay concise.",
    }
    payload["history"] = history
    return payload


def _run_bootstrap(start_payload: dict[str, object]) -> tuple[bool, SessionState, RecordingWebSocket]:
    """Run start bootstrap on a new session and return what it reported, stored, and sent."""
    state = SessionState(meta={})
    websocket = RecordingWebSocket()
    with use_local_tokenizers() as tokenizer:
        is_successful = asyncio.run(
            bootstrap_start_turn(
                typed_websocket(websocket),
                start_payload,
                state,
                session_runtime=build_session_runtime(tokenizer),
            ),
        )
    return is_successful, state, websocket


def test_history_user_bootstrap() -> None:
    """Test bootstrap start imports user-first history."""
    is_successful, state, websocket = _run_bootstrap(_start_payload(HISTORY_PAYLOAD[:2]))

    if is_successful is not True:
        pytest.fail("Assertion failed")
    if state.active_request_task is not None:
        pytest.fail("Assertion failed")
    assert state.history_messages == [MESSAGES[0], MESSAGES[1]]
    assert json.loads(websocket.sent[-1]) == {"type": "done", "status": 200}


def test_history_assistant_bootstrap() -> None:
    """Test bootstrap start imports assistant-first history."""
    is_successful, state, websocket = _run_bootstrap(_start_payload(ASSISTANT_FIRST_PAYLOAD[:4]))

    if is_successful is not True:
        pytest.fail("Assertion failed")
    assert state.history_messages == ASSISTANT_FIRST_MESSAGES[:4]
    assert json.loads(websocket.sent[-1]) == {"type": "done", "status": 200}


def test_history_payload_rejection() -> None:
    """Test bootstrap start rejects invalid history payload."""
    is_successful, _, websocket = _run_bootstrap({"history": HISTORY_PAYLOAD[:2]})

    if is_successful is not False:
        pytest.fail("Assertion failed")
    if websocket.is_closed is not True:
        pytest.fail("Assertion failed")
    assert any("invalid_payload" in payload for payload in websocket.sent)


def test_plan_committed_history() -> None:
    """Test message planning uses the session's committed history."""
    session_runtime = build_session_runtime(build_local_tokenizer())
    state = SessionState(meta={"prompt": "Stay concise."})
    session_runtime.initialize_session(state)
    state.meta["prompt"] = "Stay concise."
    state.history_messages = [
        HistoryMessage(role="user", content="hello can you help me plan a trip"),
        HistoryMessage(role="assistant", content="sure tell me your budget"),
    ]

    plan = asyncio.run(
        plan_message_turn(
            typed_websocket(RecordingWebSocket()),
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
    session_runtime = build_session_runtime(build_local_tokenizer())
    state = build_session_state(session_runtime)
    websocket = RecordingWebSocket()

    plan = asyncio.run(
        plan_message_turn(
            typed_websocket(websocket),
            {"user_utterance": "  "},
            state,
            session_runtime=session_runtime,
        ),
    )

    if plan is not None:
        pytest.fail("Assertion failed")
    assert any("user_utterance is required" in payload for payload in websocket.sent)
