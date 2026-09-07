"""Public WebSocket and loopback probe application construction."""

from __future__ import annotations

import time
import logging
import contextlib
from typing import TYPE_CHECKING
from src.logging import configure_logging
from fastapi.responses import JSONResponse
from src.state.readiness import ReadinessState
from src.telemetry.sentry import capture_error
from fastapi import FastAPI, Request, WebSocket
from src.runtime.validation import validate_settings
from src.websocket.connections import ConnectionRegistry
from src.runtime.bootstrap import build_runtime_dependencies
from src.websocket.endpoint import handle_websocket_connection
from src.telemetry.instruments import get_metrics, initialize_metrics
from src.telemetry.lifecycle import initialize_telemetry, shutdown_telemetry

if TYPE_CHECKING:
    from src.telemetry.gpu import GPUProvider
    from src.runtime.bootstrap import EngineBuilder
    from contextlib import AbstractAsyncContextManager
    from src.state.settings import ApplicationSettings
    from collections.abc import AsyncGenerator, Callable

logger = logging.getLogger(__name__)

configure_logging()


async def _shutdown_runtime(application: FastAPI) -> None:
    """Shutdown runtime dependencies and telemetry."""
    runtime_dependencies = getattr(application.state, "runtime_dependencies", None)
    try:
        if runtime_dependencies is not None:
            await runtime_dependencies.shutdown()
    finally:
        shutdown_telemetry()


def _build_public_lifespan(
    settings: ApplicationSettings,
    engine_builder: EngineBuilder,
    gpu_provider: GPUProvider | None,
    readiness_state: ReadinessState,
) -> Callable[[FastAPI], AbstractAsyncContextManager[None]]:
    """Build the public application lifespan manager."""

    @contextlib.asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncGenerator[None, None]:
        """Initialize runtime dependencies and drain them on shutdown."""
        start_time = time.monotonic()
        readiness_state.start_initializing()
        validate_settings(settings)
        initialize_telemetry()
        initialize_metrics(gpu_provider)

        try:
            runtime_dependencies = await build_runtime_dependencies(
                settings,
                connections=ConnectionRegistry(
                    maximum_connections=settings.websocket.maximum_connections,
                    acquire_timeout_seconds=settings.websocket.handshake_acquire_timeout_seconds,
                ),
                engine_builder=engine_builder,
            )
        except Exception as exception:
            capture_error(exception, extra={"phase": "bootstrap"})
            raise
        application.state.runtime_dependencies = runtime_dependencies
        readiness_state.is_runtime_initialized = True

        if runtime_dependencies.can_reset_cache():
            runtime_dependencies.start_cache_reset_daemon()
        else:
            logger.info("cache reset daemon: disabled (TRT-LLM uses block reuse)")

        get_metrics().startup_duration.record(time.monotonic() - start_time)
        try:
            yield
        finally:
            readiness_state.start_draining()
            await _shutdown_runtime(application)

    return lifespan


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Process one public WebSocket connection."""
    runtime_dependencies = getattr(websocket.app.state, "runtime_dependencies", None)
    if runtime_dependencies is None:
        message = "Runtime dependencies are not initialized"
        raise RuntimeError(message)
    await handle_websocket_connection(websocket, runtime_dependencies)


async def probe_status(request: Request) -> JSONResponse:
    """Report event-loop health or public runtime readiness."""
    if request.url.path == "/healthz":
        return JSONResponse({"status": "alive"})
    readiness_state: ReadinessState = request.app.state.readiness_state
    if readiness_state.is_ready:
        return JSONResponse({"status": "ready"})
    return JSONResponse({"status": "not_ready"}, status_code=503)


def create_public_application(
    settings: ApplicationSettings,
    engine_builder: EngineBuilder,
    *,
    gpu_provider: GPUProvider | None = None,
    readiness_state: ReadinessState | None = None,
    is_lifecycle_enabled: bool = True,
) -> FastAPI:
    """Create the public WebSocket-only application."""
    active_readiness_state = ReadinessState() if readiness_state is None else readiness_state
    lifespan = (
        _build_public_lifespan(
            settings,
            engine_builder,
            gpu_provider,
            active_readiness_state,
        )
        if is_lifecycle_enabled
        else None
    )
    application = FastAPI(docs_url=None, redoc_url=None, openapi_url=None, lifespan=lifespan)
    application.state.settings = settings
    application.state.runtime_dependencies = None
    application.state.readiness_state = active_readiness_state
    application.websocket("/ws")(websocket_endpoint)
    return application


def create_probe_application(readiness_state: ReadinessState) -> FastAPI:
    """Create the fixed loopback health and readiness application."""
    application = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    application.state.readiness_state = readiness_state
    application.get("/healthz")(probe_status)
    application.get("/readyz")(probe_status)
    return application


__all__ = [
    "create_probe_application",
    "create_public_application",
    "probe_status",
    "websocket_endpoint",
]
