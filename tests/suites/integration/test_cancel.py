"""Integration tests for websocket cancel and recovery behavior."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
import asyncio
from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import patch

from tests.state import SessionContext
from src.execution.turn import StreamResponseRequest, stream_response
from src.runtime.config import HistorySettings
from tests.harness.client.websocket import build_start_payload, build_cancel_payload, build_message_payload
from tests.suites.integration.builders import TEST_API_KEY, AUTHENTICATED_SETTINGS, open_test_client

if TYPE_CHECKING:
    from collections.abc import Generator, AsyncIterator

    from fastapi import WebSocket
    from fastapi.testclient import TestClient
    from starlette.testclient import WebSocketTestSession

    from src.execution.turn import TurnRequest
    from src.runtime.dependencies import RuntimeDependencies


async def _stream_test_turn(websocket: WebSocket, plan: TurnRequest, runtime_dependencies: RuntimeDependencies) -> None:
    chunks_by_prompt = {
        "cancel me": ("cancel-alpha", "cancel-beta"),
        "recover now": ("recover-alpha", "recover-beta"),
    }
    first, second = chunks_by_prompt.get(plan.user_utterance or "", ("generic-alpha", "generic-beta"))

    async def _stream() -> AsyncIterator[str]:
        yield first
        await asyncio.sleep(0.05)
        yield second

    await stream_response(
        StreamResponseRequest(
            websocket=websocket,
            stream=_stream(),
            connection_state=plan.state,
            user_utterance=plan.user_utterance or "",
            history_user_utterance=plan.user_utterance or "",
            session_runtime=runtime_dependencies.session_runtime,
        ),
    )


@contextmanager
def _test_client() -> Generator[TestClient, None, None]:
    session_settings = replace(AUTHENTICATED_SETTINGS, history=HistorySettings(trigger_tokens=1000, target_tokens=800))
    with (
        patch("src.messages.turn.run_turn_execution", _stream_test_turn),
        open_test_client(AUTHENTICATED_SETTINGS, session_settings=session_settings) as client,
    ):
        yield client


def _receive_json(websocket: WebSocketTestSession) -> dict[str, object]:
    return json.loads(websocket.receive_text())


def _build_context() -> SessionContext:
    return SessionContext(
        session_id="integration-cancel",
        gender="female",
        personality="calm",
        prompt="Stay concise.",
    )


def test_cancel_recovery() -> None:
    """Test start bootstraps then cancelled turn recovers cleanly."""
    with _test_client() as client, client.websocket_connect("/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
        context = _build_context()

        websocket.send_text(json.dumps(build_start_payload(context)))
        bootstrap_done = _receive_json(websocket)
        assert bootstrap_done == {"type": "done", "status": 200}

        websocket.send_text(json.dumps(build_message_payload("cancel me")))
        first_token = _receive_json(websocket)
        assert first_token == {"type": "token", "text": "cancel-alpha"}

        websocket.send_text(json.dumps(build_cancel_payload()))
        is_cancelled = _receive_json(websocket)
        assert is_cancelled == {"type": "cancelled"}

        websocket.send_text(json.dumps(build_message_payload("recover now")))
        recovery_token = _receive_json(websocket)
        assert recovery_token == {"type": "token", "text": "recover-alpha"}

        second_recovery_token = _receive_json(websocket)
        assert second_recovery_token == {"type": "token", "text": "recover-beta"}

        recovery_completion = _receive_json(websocket)
        assert recovery_completion["type"] == "final"
        assert recovery_completion["text"] == "recover-alpharecover-beta"

        recovery_done = _receive_json(websocket)
        assert recovery_done == {"type": "done", "status": 200}


def test_early_cancel_allows_bootstrap() -> None:
    """Cancelling an idle connection must leave session bootstrap available."""
    with _test_client() as client, client.websocket_connect("/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
        websocket.send_text(json.dumps(build_cancel_payload()))
        assert _receive_json(websocket)["type"] == "cancelled"

        websocket.send_text(json.dumps(build_start_payload(_build_context())))
        assert _receive_json(websocket)["type"] == "done"

        websocket.send_text(json.dumps(build_message_payload("recover now")))
        response_types = [_receive_json(websocket)["type"] for _ in range(4)]
        assert response_types == ["token", "token", "final", "done"]
