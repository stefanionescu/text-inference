"""Integration tests for websocket idle-timeout behavior."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING
from contextlib import AbstractContextManager, contextmanager
from dataclasses import replace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.server import create_public_application
import src.session.runtime as session_runtime_module
from config.runtime.websocket import WEBSOCKET_CLOSE_IDLE_CODE, WEBSOCKET_PROTOCOL_VERSION, WEBSOCKET_CLOSE_IDLE_REASON
from src.runtime.dependencies import RuntimeDependencies
from src.websocket.connections import ConnectionRegistry
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS
from tests.harness.environment.tokenizer import use_local_tokenizers

if TYPE_CHECKING:
    from collections.abc import Generator

    from src.runtime.config import ApplicationSettings

TEST_API_KEY = "integration-test-key"


def _test_settings() -> ApplicationSettings:
    return replace(
        DEFAULT_APPLICATION_SETTINGS,
        authentication=replace(DEFAULT_APPLICATION_SETTINGS.authentication, api_key=TEST_API_KEY),
        websocket=replace(
            DEFAULT_APPLICATION_SETTINGS.websocket,
            idle_timeout_seconds=0.2,
            watchdog_tick_seconds=0.02,
        ),
    )


def _build_runtime_dependencies(
    settings: ApplicationSettings,
) -> tuple[RuntimeDependencies, AbstractContextManager[object]]:
    tokenizer_cm = use_local_tokenizers()
    tokenizer = tokenizer_cm.__enter__()
    engine = AsyncMock()
    engine.can_reset_cache = False
    runtime_dependencies = RuntimeDependencies(
        connections=ConnectionRegistry(
            maximum_connections=4, acquire_timeout_seconds=settings.websocket.handshake_acquire_timeout_seconds
        ),
        session_runtime=session_runtime_module.SessionRuntime(settings=settings, tokenizer=tokenizer),
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
        with TestClient(application) as client:
            yield client
    finally:
        tokenizer_cm.__exit__(None, None, None)


def test_idle_close_code() -> None:
    """Test idle connection closes with expected code and reason."""
    with _test_client() as client, client.websocket_connect("/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
        close_frame = websocket.receive()

    assert close_frame["type"] == "websocket.close"
    assert close_frame["code"] == WEBSOCKET_CLOSE_IDLE_CODE
    assert close_frame["reason"] == WEBSOCKET_CLOSE_IDLE_REASON


def test_activity_keeps_alive() -> None:
    """Test activity keeps connection alive until explicit end."""
    with _test_client() as client, client.websocket_connect("/ws", headers={"X-API-Key": TEST_API_KEY}) as websocket:
        websocket.send_text(json.dumps({"type": "ping", "v": WEBSOCKET_PROTOCOL_VERSION}))
        assert json.loads(websocket.receive_text()) == {"type": "pong"}

        websocket.send_text(json.dumps({"type": "end", "v": WEBSOCKET_PROTOCOL_VERSION}))
        assert json.loads(websocket.receive_text()) == {"type": "done", "status": 200}
