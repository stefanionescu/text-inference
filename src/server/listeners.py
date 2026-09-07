"""Run the public and loopback ASGI listeners."""

from __future__ import annotations

import asyncio
import uvicorn
from typing import TYPE_CHECKING
from config.runtime import listeners
from src.server.probe import ProbeServer

if TYPE_CHECKING:
    import socket
    from fastapi import FastAPI
    from src.state.readiness import ReadinessState


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
    probe_application: FastAPI,
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
    probe_server = ProbeServer(
        _build_server_config(
            probe_application,
            listeners.PROBE_SERVER_HOST,
            listeners.PROBE_SERVER_PORT,
            is_logging_enabled=False,
            lifespan="off",
        ),
    )
    public_task = asyncio.create_task(public_server.serve())
    probe_task = asyncio.create_task(probe_server.serve())
    try:
        done, _ = await asyncio.wait({public_task, probe_task}, return_when=asyncio.FIRST_COMPLETED)
        if public_task in done:
            probe_server.should_exit = True
        if probe_task in done:
            public_server.should_exit = True
        await asyncio.gather(public_task, probe_task)
    finally:
        readiness_state.start_draining()


def run_applications(
    public_application: FastAPI,
    probe_application: FastAPI,
    readiness_state: ReadinessState,
    *,
    is_logging_enabled: bool,
) -> None:
    """Run both listeners in the process event loop."""
    asyncio.run(
        serve_applications(
            public_application,
            probe_application,
            readiness_state,
            is_logging_enabled=is_logging_enabled,
        ),
    )


__all__ = ["run_applications", "serve_applications"]
