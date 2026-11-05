"""Integration tests for websocket cancel and recovery behavior."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
import asyncio
from contextlib import AbstractContextManager, contextmanager
from dataclasses import replace
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.server import create_public_application
from tests.state import SessionContext
from src.execution.turn import StreamResponseRequest, stream_response
from src.runtime.config import HistorySettings
from src.session.runtime import SessionRuntime
from src.runtime.dependencies import RuntimeDependencies
from src.websocket.connections import ConnectionRegistry
from tests.harness.client.websocket import build_start_payload, build_cancel_payload, build_message_payload
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS
from tests.harness.environment.tokenizer import use_local_tokenizers

if TYPE_CHECKING:
    from collections.abc import Generator, AsyncIterator

    from fastapi import WebSocket
    from starlette.testclient import WebSocketTestSession

    from src.execution.turn import TurnRequest
    from src.runtime.config import ApplicationSettings

TEST_API_KEY = "integration-test-key"


def _test_settings() -> ApplicationSettings:
    return replace(
        DEFAULT_APPLICATION_SETTINGS,
        authentication=replace(DEFAULT_APPLICATION_SETTINGS.authentication, api_key=TEST_API_KEY),
    )


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


def _build_runtime_dependencies(
    settings: ApplicationSettings,
) -> tuple[RuntimeDependencies, AbstractContextManager[object]]:
    tokenizer_cm = use_local_tokenizers()
    tokenizer = tokenizer_cm.__enter__()
    engine = AsyncMock()
    engine.can_reset_cache = False
    session_runtime = SessionRuntime(
        tokenizer=tokenizer,
        settings=replace(settings, history=HistorySettings(trigger_tokens=1000, target_tokens=800)),
    )
    runtime_dependencies = RuntimeDependencies(
        connections=ConnectionRegistry(
            maximum_connections=4, acquire_timeout_seconds=settings.websocket.handshake_acquire_timeout_seconds
        ),
        session_runtime=session_runtime,
        engine=engine,
        cache_reset_coordinator=None,
        tokenizer=tokenizer,
        settings=settings,
    )
    return runtime_dependencies, tokenizer_cm


@contextmanager
def _test_client() -> Generator[TestClient, None, None]:
    settings = _test_settings()
    runtime_dependencies, tokenizer_cm = _build_runtime_dependencies(settings)
    application = create_public_application(settings, AsyncMock(), is_lifecycle_enabled=False)
    application.state.runtime_dependencies = runtime_dependencies

    try:
        with patch("src.messages.turn.run_turn_execution", _stream_test_turn), TestClient(application) as client:
            yield client
    finally:
        tokenizer_cm.__exit__(None, None, None)


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


def test_cancel_before_start_allows_session_bootstrap() -> None:
    """Cancelling an idle connection must leave session bootstrap available."""
    with _test_client() as client, client.websocket_connect("/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
        websocket.send_text(json.dumps(build_cancel_payload()))
        assert _receive_json(websocket)["type"] == "cancelled"

        websocket.send_text(json.dumps(build_start_payload(_build_context())))
        assert _receive_json(websocket)["type"] == "done"

        websocket.send_text(json.dumps(build_message_payload("recover now")))
        response_types = [_receive_json(websocket)["type"] for _ in range(4)]
        assert response_types == ["token", "token", "final", "done"]
