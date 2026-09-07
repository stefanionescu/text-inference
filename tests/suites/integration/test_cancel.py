"""Integration tests for websocket cancel and recovery behavior."""

from __future__ import annotations

import json
import asyncio
from dataclasses import replace
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock
from tests.state import SessionContext
from fastapi.testclient import TestClient
from src.session.runtime import SessionRuntime
from src.state.settings import HistorySettings
from src.server import create_public_application
from src.runtime import DEFAULT_APPLICATION_SETTINGS
from src.runtime.dependencies import RuntimeDependencies
from src.websocket.connections import ConnectionRegistry
from contextlib import AbstractContextManager, contextmanager
from tests.harness.environment.tokenizer import use_local_tokenizers
from src.websocket.transport import StreamResponseRequest, stream_response
from tests.harness.client.websocket import build_cancel_payload, build_message_payload, build_start_payload

if TYPE_CHECKING:
    from fastapi import WebSocket
    from src.state.turn import TurnPlan
    from src.state.settings import ApplicationSettings
    from collections.abc import AsyncIterator, Generator
    from starlette.testclient import WebSocketTestSession

TEST_API_KEY = "integration-test-key"


def _test_settings() -> ApplicationSettings:
    return replace(
        DEFAULT_APPLICATION_SETTINGS,
        authentication=replace(DEFAULT_APPLICATION_SETTINGS.authentication, api_key=TEST_API_KEY),
    )


async def _stream_test_turn(websocket: WebSocket, plan: TurnPlan, runtime_dependencies: RuntimeDependencies) -> None:
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
        settings=settings,
        engine=engine,
        tokenizer=tokenizer,
        history_config=HistorySettings(trigger_tokens=1000, target_tokens=800),
    )
    runtime_dependencies = RuntimeDependencies(
        connections=ConnectionRegistry(maximum_connections=4),
        session_runtime=session_runtime,
        engine=engine,
        cache_reset_coordinator=None,
        tokenizer=tokenizer,
        settings=settings,
        turn_dispatch=_stream_test_turn,
    )
    return runtime_dependencies, tokenizer_cm


@contextmanager
def _test_client() -> Generator[TestClient, None, None]:
    settings = _test_settings()
    runtime_dependencies, tokenizer_cm = _build_runtime_dependencies(settings)
    application = create_public_application(settings, AsyncMock(), is_lifecycle_enabled=False)
    application.state.runtime_dependencies = runtime_dependencies

    try:
        with TestClient(application) as client:
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
