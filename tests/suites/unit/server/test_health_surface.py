"""Unit tests for public-route isolation and internal probes."""

from __future__ import annotations

from http import HTTPStatus
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from src.state.readiness import ReadinessState
from src.runtime import DEFAULT_APPLICATION_SETTINGS
from src.server import create_probe_application, create_public_application

NOT_FOUND_STATUS = 404
NOT_READY_STATUS = 503


def test_public_route_isolation() -> None:
    """Test public listener exposes neither probes nor documentation."""
    application = create_public_application(
        DEFAULT_APPLICATION_SETTINGS,
        AsyncMock(),
        is_lifecycle_enabled=False,
    )

    with TestClient(application) as client:
        for path in ("/healthz", "/readyz", "/docs", "/redoc", "/openapi.json"):
            assert client.get(path).status_code == NOT_FOUND_STATUS


def test_health_alive() -> None:
    """Test health reports the probe process event loop independently of readiness."""
    status = ReadinessState()

    with TestClient(create_probe_application(status)) as client:
        response = client.get("/healthz")

    assert response.status_code == HTTPStatus.OK
    assert response.json() == {"status": "alive"}


def test_readiness_transitions() -> None:
    """Test readiness stays false until serving and falls before draining."""
    status = ReadinessState()

    with TestClient(create_probe_application(status)) as client:
        assert client.get("/readyz").status_code == NOT_READY_STATUS
        status.is_runtime_initialized = True
        assert client.get("/readyz").status_code == NOT_READY_STATUS
        status.is_public_accepting = True
        assert client.get("/readyz").status_code == HTTPStatus.OK
        status.start_draining()
        assert client.get("/readyz").status_code == NOT_READY_STATUS
