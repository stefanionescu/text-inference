"""Unit tests for session history accounting invariants."""

from __future__ import annotations
import pytest
from dataclasses import replace
from unittest.mock import AsyncMock
from src.runtime.config import HistorySettings
from src.session.runtime import SessionRuntime
from src.tokens.tokenizer import ThreadSafeTokenizer
from src.session.state import HistoryMessage, SessionState
import src.session.history.transcript as history_transcript
from tests.harness.environment.tokenizer import use_local_tokenizers
from tests.harness.messages.unit import ASSISTANT_FIRST_MESSAGES, MESSAGES
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS

EXPECTED_MESSAGE_COUNT = 4
TURN_MESSAGE_COUNT = 2


def _history_config(
    *,
    trigger_tokens: int = 1000,
    target_tokens: int = 800,
) -> HistorySettings:
    trigger = int(trigger_tokens)
    target = int(target_tokens)
    if trigger < 0 or target < 0:
        raise ValueError
    return HistorySettings(
        trigger_tokens=trigger,
        target_tokens=target,
    )


def _make_state(session_runtime: SessionRuntime) -> SessionState:
    state = SessionState(meta={})
    session_runtime.initialize_session(state)
    return state


def _build_session(
    *,
    trigger_tokens: int = 1000,
    target_tokens: int = 800,
    tokenizer: ThreadSafeTokenizer,
) -> SessionRuntime:
    AsyncMock()
    history_config = _history_config(
        trigger_tokens=trigger_tokens,
        target_tokens=target_tokens,
    )
    return SessionRuntime(
        tokenizer=tokenizer,
        settings=replace(DEFAULT_APPLICATION_SETTINGS, history=history_config),
    )


def test_history_ingest_flows() -> None:
    """Test history append, import, and merge flows."""
    with use_local_tokenizers() as tokenizer:
        session_runtime = _build_session(tokenizer=tokenizer)
        state = _make_state(session_runtime)

        rendered = session_runtime.history.append_response(state, "hello", "world")

        assert state.history_messages is not None
        assert [(message.role, message.content) for message in state.history_messages] == [
            ("user", "hello"),
            ("assistant", "world"),
        ]
        if "User: hello" not in rendered:
            pytest.fail("Assertion failed")
        if "Assistant: world" not in rendered:
            pytest.fail("Assertion failed")
    with use_local_tokenizers() as tokenizer:
        session_runtime = _build_session(tokenizer=tokenizer)
        state = _make_state(session_runtime)

        messages = [*MESSAGES[:3], HistoryMessage(role="assistant", content="reply")]

        rendered = session_runtime.history.set_mode_histories(state, history_messages=messages)

        if "User: hello can you help me plan a trip to lisbon next week" not in rendered:
            pytest.fail("Assertion failed")
        if "Assistant: reply" not in rendered:
            pytest.fail("Assertion failed")
        assert state.history_messages is not None
        assert len(state.history_messages) == EXPECTED_MESSAGE_COUNT
    with use_local_tokenizers() as tokenizer:
        session_runtime = _build_session(tokenizer=tokenizer)
        state = _make_state(session_runtime)
        state.history_messages = [HistoryMessage(role="user", content="seed")]

        session_runtime.history.append_response(state, "follow up", "reply")

        assert state.history_messages is not None
        assert [(message.role, message.content) for message in state.history_messages] == [
            ("user", "seed\n\nfollow up"),
            ("assistant", "reply"),
        ]


def test_history_trimming_flows() -> None:
    """Test eager trimming and assistant-first grouping."""
    with use_local_tokenizers() as tokenizer:
        session_runtime = _build_session(trigger_tokens=10, target_tokens=6, tokenizer=tokenizer)
        state = _make_state(session_runtime)

        turns = [
            ("hello how are you", "great"),
            ("alpha bravo charlie", "one two"),
            ("hello world", "three four"),
            ("u1 u2 u3", "a1 a2"),
        ]
        for user_text, assistant_text in turns:
            session_runtime.history.append_response(state, user_text, assistant_text)

        assert state.history_messages is not None
        assert len(state.history_messages) < len(turns) * TURN_MESSAGE_COUNT
        assert state.history_messages[0].role == "user"
        assert len(state.history_messages) % 2 == 0
    with use_local_tokenizers() as tokenizer:
        session_runtime = _build_session(trigger_tokens=8, target_tokens=4, tokenizer=tokenizer)
        state = _make_state(session_runtime)

        session_runtime.history.append_response(state, "hello how are you", "great")
        session_runtime.history.append_response(state, "alpha bravo charlie", "one two three")

        assert state.history_messages is not None
        assert [(message.role, message.content) for message in state.history_messages] == [
            ("user", "alpha bravo charlie"),
            ("assistant", "one two three"),
        ]
    with use_local_tokenizers() as tokenizer:
        state = SessionState(meta={})
        state.history_messages = list(ASSISTANT_FIRST_MESSAGES)

        history_transcript.trim_history(
            state,
            config=_history_config(
                trigger_tokens=60,
                target_tokens=40,
            ),
            tokenizer=tokenizer,
        )

        assert state.history_messages == ASSISTANT_FIRST_MESSAGES[-2:]


class _SpecialAwareTokenizer(ThreadSafeTokenizer):
    def __init__(self) -> None:
        """Skip external tokenizer initialization for this test double."""

    def count(self, text: str, *, are_special_tokens_added: bool = False) -> int:
        """Test count."""
        if not text.strip():
            return 0
        total = len(text.split())
        if are_special_tokens_added:
            total += 2
        return total

    def trim(self, text: str, maximum_tokens: int, retained_side: str = "end") -> str:
        """Test trim."""
        tokens = text.split()
        if maximum_tokens <= 0:
            return ""
        if len(tokens) <= maximum_tokens:
            return text
        retained_tokens = tokens[:maximum_tokens] if retained_side == "start" else tokens[-maximum_tokens:]
        return " ".join(retained_tokens)

    def encode_ids(self, text: str) -> list[int]:
        """Test encode ids."""
        tokens = text.split()
        token_count = len(tokens)
        return list(range(token_count))


def test_history_uses_tokenizer() -> None:
    """Trim history using the supplied tokenizer's token counts."""
    messages = [
        HistoryMessage(role="user", content="one"),
        HistoryMessage(role="assistant", content="two"),
        HistoryMessage(role="user", content="three"),
        HistoryMessage(role="assistant", content="four"),
    ]
    state = SessionState(meta={}, history_messages=messages)
    history_transcript.trim_history(
        state,
        config=HistorySettings(trigger_tokens=6, target_tokens=4),
        tokenizer=_SpecialAwareTokenizer(),
    )
    assert state.history_messages == messages[-2:]
