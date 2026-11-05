"""Unit tests for start-message history helpers."""

from __future__ import annotations

import pytest

from src.session.state import SessionState, HistoryMessage
from src.messages.start import history_messages
from tests.suites.unit.builders import build_session_state, build_session_runtime
from tests.harness.messages.unit import MESSAGES, HISTORY_PAYLOAD, ASSISTANT_FIRST_PAYLOAD, ASSISTANT_FIRST_MESSAGES
from tests.harness.environment.tokenizer import use_local_tokenizers

TRIM_TRIGGER_TOKENS = 6
TRIM_TARGET_TOKENS = 4
FRESH_HISTORY_TURNS = 2
ASSISTANT_FIRST_TURNS = 4


def _history_turn_count(state: SessionState) -> int:
    messages = state.history_messages
    if messages is not None:
        return len(messages)
    return 0


def test_history_seed_flows() -> None:
    """Test history import, trimming, and fresh-session seeding."""
    with use_local_tokenizers() as tokenizer:
        session_runtime = build_session_runtime(tokenizer)
        state = build_session_state(session_runtime)
        message = {"history": HISTORY_PAYLOAD[:4]}

        messages = history_messages(session_runtime, state, message)

        assert messages == MESSAGES[:4]
        assert state.history_messages == MESSAGES[:4]
    with use_local_tokenizers() as tokenizer:
        session_runtime = build_session_runtime(
            tokenizer,
            trigger_tokens=TRIM_TRIGGER_TOKENS,
            target_tokens=TRIM_TARGET_TOKENS,
        )
        state = build_session_state(session_runtime)
        message = {
            "history": [
                {"role": "user", "content": "u1"},
                {"role": "assistant", "content": "a1"},
                {"role": "user", "content": "u2"},
                {"role": "assistant", "content": "a2"},
                {"role": "user", "content": "u3"},
                {"role": "assistant", "content": "a3"},
            ],
        }

        messages = history_messages(session_runtime, state, message)

        assert state.history_messages is not None
        assert len(state.history_messages) < TRIM_TRIGGER_TOKENS
        assert messages == state.history_messages
    with use_local_tokenizers() as tokenizer:
        session_runtime = build_session_runtime(tokenizer)
        state = build_session_state(session_runtime)

        assert _history_turn_count(state) == 0

        messages = history_messages(
            session_runtime,
            state,
            {
                "history": [
                    {"role": "user", "content": "hello"},
                    {"role": "assistant", "content": "hi there"},
                ],
            },
        )

        assert messages == [
            HistoryMessage(role="user", content="hello"),
            HistoryMessage(role="assistant", content="hi there"),
        ]
        assert _history_turn_count(state) == FRESH_HISTORY_TURNS
    with use_local_tokenizers() as tokenizer:
        session_runtime = build_session_runtime(tokenizer)
        state = build_session_state(session_runtime)

        messages = history_messages(session_runtime, state, {"history": ASSISTANT_FIRST_PAYLOAD[:4]})

        assert messages == ASSISTANT_FIRST_MESSAGES[:4]
        assert state.history_messages == ASSISTANT_FIRST_MESSAGES[:4]
        assert _history_turn_count(state) == ASSISTANT_FIRST_TURNS


def test_history_merge_flows() -> None:
    """Test late history handling, group trimming, and user merges."""
    with use_local_tokenizers() as tokenizer:
        session_runtime = build_session_runtime(tokenizer)
        state = build_session_state(session_runtime)

        first_messages = history_messages(
            session_runtime,
            state,
            {
                "history": [
                    {"role": "user", "content": "first hello"},
                    {"role": "assistant", "content": "first hi"},
                ],
            },
        )
        assert any(message.content == "first hello" for message in first_messages)

        session_runtime.history.append_response(state, "follow-up", "")
        assert _history_turn_count(state) > 0

        second_messages = history_messages(
            session_runtime,
            state,
            {
                "history": [
                    {"role": "user", "content": "OVERWRITE ATTEMPT"},
                    {"role": "assistant", "content": "OVERWRITE ATTEMPT"},
                ],
            },
        )

        if any("OVERWRITE ATTEMPT" in message.content for message in second_messages):
            pytest.fail("Assertion failed")
        assert any(message.content == "first hello" for message in second_messages)
    with use_local_tokenizers() as tokenizer:
        session_runtime = build_session_runtime(tokenizer, trigger_tokens=60, target_tokens=40)
        state = build_session_state(session_runtime)

        messages = history_messages(session_runtime, state, {"history": ASSISTANT_FIRST_PAYLOAD})

        assert messages == ASSISTANT_FIRST_MESSAGES[-2:]
        assert state.history_messages == ASSISTANT_FIRST_MESSAGES[-2:]
    with use_local_tokenizers() as tokenizer:
        session_runtime = build_session_runtime(tokenizer)
        state = build_session_state(session_runtime)

        messages = history_messages(
            session_runtime,
            state,
            {
                "history": [
                    {"role": "user", "content": "one"},
                    {"role": "user", "content": "two"},
                    {"role": "assistant", "content": "reply"},
                ],
            },
        )

        assert messages == [
            HistoryMessage(role="user", content="one\n\ntwo"),
            HistoryMessage(role="assistant", content="reply"),
        ]
