"""Public and loopback ASGI listeners with shared signal ownership."""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
import contextlib

import uvicorn

from config.runtime import listeners

if TYPE_CHECKING:
    from collections.abc import Generator


class ReadinessServer(uvicorn.Server):
    """Run without competing for process signal ownership."""

    def install_signal_handlers(self) -> None:
        """Leave signal ownership with the public server."""

    @contextlib.contextmanager
    def capture_signals(self) -> Generator[None, None, None]:
        """Leave signal ownership with the public server."""
        yield


if TYPE_CHECKING:
    import socket

    from fastapi import FastAPI

    from src.runtime.config import ApplicationSettings
    from src.server.readiness import ReadinessState


class _PublicServer(uvicorn.Server):
    """Expose exact public socket acceptance and draining transitions."""

    def __init__(self, config: uvicorn.Config, readiness_state: ReadinessState) -> None:
        """Initialize a public server tied to shared readiness state."""
        super().__init__(config)
        self._readiness_state = readiness_state

    async def startup(self, sockets: list[socket.socket] | None = None) -> None:
        """Mark readiness only after the public socket starts accepting."""
        await super().startup(sockets=sockets)
        if self.started and not self._readiness_state.is_draining:
            self._readiness_state.is_public_accepting = True

    async def shutdown(self, sockets: list[socket.socket] | None = None) -> None:
        """Withdraw readiness before the public listener begins draining."""
        self._readiness_state.start_draining()
        await super().shutdown(sockets=sockets)


def _build_server_config(
    application: FastAPI,
    host: str,
    port: int,
    *,
    is_logging_enabled: bool,
    lifespan: str,
) -> uvicorn.Config:
    """Build one fixed single-worker server configuration."""
    return uvicorn.Config(
        application,
        host=host,
        port=port,
        workers=1,
        access_log=is_logging_enabled,
        log_level="info" if is_logging_enabled else "warning",
        lifespan=lifespan,
    )


async def serve_applications(
    public_application: FastAPI,
    readiness_application: FastAPI,
    readiness_state: ReadinessState,
    *,
    is_logging_enabled: bool,
) -> None:
    """Serve both listeners until either server stops."""
    public_server = _PublicServer(
        _build_server_config(
            public_application,
            ".".join(listeners.PUBLIC_SERVER_HOST_OCTETS),
            listeners.PUBLIC_SERVER_PORT,
            is_logging_enabled=is_logging_enabled,
            lifespan="on",
        ),
        readiness_state,
    )
    readiness_server = ReadinessServer(
        _build_server_config(
            readiness_application,
            listeners.READINESS_SERVER_HOST,
            listeners.READINESS_SERVER_PORT,
            is_logging_enabled=False,
            lifespan="off",
        ),
    )
    public_task = asyncio.create_task(public_server.serve())
    readiness_task = asyncio.create_task(readiness_server.serve())
    try:
        done, _ = await asyncio.wait({public_task, readiness_task}, return_when=asyncio.FIRST_COMPLETED)
        if public_task in done:
            readiness_server.should_exit = True
        if readiness_task in done:
            public_server.should_exit = True
        await asyncio.gather(public_task, readiness_task)
    finally:
        readiness_state.start_draining()


def run_applications(
    public_application: FastAPI,
    readiness_application: FastAPI,
    readiness_state: ReadinessState,
    *,
    settings: ApplicationSettings,
) -> None:
    """Run both listeners in the process event loop."""
    asyncio.run(
        serve_applications(
            public_application,
            readiness_application,
            readiness_state,
            is_logging_enabled=settings.engine.is_logging_enabled,
        ),
    )


__all__ = ["ReadinessServer", "run_applications", "serve_applications"]
