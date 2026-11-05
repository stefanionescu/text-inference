"""Application builders for websocket integration tests."""

from __future__ import annotations

from typing import TYPE_CHECKING
from contextlib import contextmanager
from dataclasses import replace
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient

from src.session.runtime import SessionRuntime
from src.server.applications import create_public_application
from src.runtime.dependencies import RuntimeDependencies
from src.websocket.connections import ConnectionRegistry
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS
from tests.harness.environment.tokenizer import use_local_tokenizers

if TYPE_CHECKING:
    from collections.abc import Generator

    from src.runtime.config import ApplicationSettings

TEST_API_KEY = "integration-test-key"
AUTHENTICATED_SETTINGS = replace(
    DEFAULT_APPLICATION_SETTINGS,
    authentication=replace(DEFAULT_APPLICATION_SETTINGS.authentication, api_key=TEST_API_KEY),
)


@contextmanager
def open_test_client(
    settings: ApplicationSettings,
    *,
    session_settings: ApplicationSettings | None = None,
) -> Generator[TestClient, None, None]:
    """Yield a client for the public app on a mock engine; session_settings override only the session runtime."""
    with use_local_tokenizers() as tokenizer:
        engine = AsyncMock()
        engine.can_reset_cache = False
        application = create_public_application(settings, AsyncMock(), is_lifecycle_enabled=False)
        application.state.runtime_dependencies = RuntimeDependencies(
            connections=ConnectionRegistry(
                maximum_connections=4,
                acquire_timeout_seconds=settings.websocket.handshake_acquire_timeout_seconds,
            ),
            session_runtime=SessionRuntime(tokenizer=tokenizer, settings=session_settings or settings),
            engine=engine,
            cache_reset_coordinator=None,
            tokenizer=tokenizer,
            settings=settings,
        )
        with TestClient(application) as client:
            yield client


__all__ = ["AUTHENTICATED_SETTINGS", "TEST_API_KEY", "open_test_client"]
