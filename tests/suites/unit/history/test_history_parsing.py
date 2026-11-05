"""History normalization through the production schema and storage boundary."""

from __future__ import annotations

import json

import pytest

from src.session.state import SessionState, HistoryMessage
from src.messages.start import history_messages
from src.session.runtime import SessionRuntime
from src.websocket.parser import parse_client_message
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS
from tests.harness.environment.tokenizer import build_local_tokenizer


def test_history_normalization() -> None:
    """Normalize roles and whitespace once while preserving message ordering."""
    parsed = parse_client_message(
        json.dumps(
            {
                "type": "start",
                "v": 1,
                "history": [
                    {"role": " ASSISTANT ", "content": " first "},
                    {"role": "assistant", "content": "second"},
                    {"role": "user", "content": " one "},
                    {"role": "user", "content": "  "},
                    {"role": "user", "content": " two "},
                ],
            }
        ),
        websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket,
    )
    runtime = SessionRuntime(tokenizer=build_local_tokenizer(), settings=DEFAULT_APPLICATION_SETTINGS)
    state = SessionState(meta={})
    imported = history_messages(runtime, state, parsed)
    assert imported == [
        HistoryMessage(role="assistant", content="first"),
        HistoryMessage(role="assistant", content="second"),
        HistoryMessage(role="user", content="one\n\ntwo"),
    ]
    assert state.history_messages == imported


@pytest.mark.parametrize("item", [42, {"role": "user"}, {"role": "system", "content": "text"}])
def test_history_shape_rejected(item: object) -> None:
    """Reject malformed and unsupported history entries at the schema boundary."""
    with pytest.raises(ValueError, match="history"):
        parse_client_message(
            json.dumps({"type": "start", "v": 1, "history": [item]}),
            websocket_settings=DEFAULT_APPLICATION_SETTINGS.websocket,
        )
