"""Connection registry for WebSocket concurrency limiting.

This module manages the pool of active WebSocket connections and enforces
the MAX_CONCURRENT_CONNECTIONS limit. It provides:

- Connection admission control (semaphore-based)
- Active connection tracking
- Capacity metrics for health checks
- Thread-safe connection add/remove operations

The connection registry uses a two-stage approach:
1. Semaphore acquisition (with timeout) to reserve a slot
2. Lock-protected set addition to track the connection

This prevents both over-admission (too many connections) and race
conditions during connection/disconnection.

Example:
    registry = ConnectionRegistry(maximum_connections=100)

    async def handle_websocket(websocket: WebSocket):
        if not await registry.connect(websocket):
            await websocket.close(code=1013)  # Try again later
            return
        try:
            # Handle messages...
        finally:
            await registry.disconnect(websocket)

"""

import time
import asyncio
import logging
from fastapi import WebSocket
from ..telemetry.instruments import get_metrics
from config.limits import MAX_CONCURRENT_CONNECTIONS
from config.runtime.websocket import WEBSOCKET_HANDSHAKE_ACQUIRE_TIMEOUT_SECONDS

logger = logging.getLogger(__name__)


class ConnectionRegistry:
    """Handles WebSocket connections and enforces concurrency limits.

    This class manages the lifecycle of WebSocket connections with:
    - Maximum connection limit enforcement
    - Timeout-based connection admission
    - Atomic connect/disconnect operations

    Attributes:
        maximum_connections: Maximum allowed concurrent connections.
        acquire_timeout_seconds: Maximum seconds to wait for a connection slot.
        active_connections: Set of currently connected WebSocket instances.

    """

    def __init__(
        self,
        maximum_connections: int | None = None,
        acquire_timeout_seconds: float = WEBSOCKET_HANDSHAKE_ACQUIRE_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize connection tracking and concurrency limits."""
        if maximum_connections is None:
            if MAX_CONCURRENT_CONNECTIONS is None:
                message = "MAX_CONCURRENT_CONNECTIONS not configured"
                raise RuntimeError(message)
            maximum_connections = MAX_CONCURRENT_CONNECTIONS
        self.maximum_connections = maximum_connections
        self.acquire_timeout_seconds = acquire_timeout_seconds
        self.active_connections: set[WebSocket] = set()
        self._lock = asyncio.Lock()  # Protects active_connections set
        self._semaphore = asyncio.Semaphore(maximum_connections)  # Limits concurrency

    async def connect(self, websocket: WebSocket) -> bool:
        """Attempt to add a new WebSocket connection.

        Args:
            websocket: WebSocket connection to add

        Returns:
            True if connection was accepted, False if at capacity

        """
        metrics = get_metrics()
        started_at = time.monotonic()
        try:
            await asyncio.wait_for(self._semaphore.acquire(), timeout=self.acquire_timeout_seconds)
        except TimeoutError:
            metrics.connection_semaphore_wait.record(time.monotonic() - started_at)
            metrics.connections_rejected_total.add(1)
            logger.warning(
                "Connection rejected: at capacity (%s/%s)",
                len(self.active_connections),
                self.maximum_connections,
            )
            return False
        metrics.connection_semaphore_wait.record(time.monotonic() - started_at)

        try:
            async with self._lock:
                self.active_connections.add(websocket)
                logger.info(
                    "Connection accepted: %s/%s active",
                    len(self.active_connections),
                    self.maximum_connections,
                )
                return True
        except Exception:
            self._semaphore.release()
            raise

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection.

        Args:
            websocket: WebSocket connection to remove

        """
        is_release_needed = False
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
                is_release_needed = True
                logger.info(
                    "Connection removed: %s/%s active",
                    len(self.active_connections),
                    self.maximum_connections,
                )
        if is_release_needed:
            self._semaphore.release()

    def get_capacity_snapshot(self) -> dict[str, int | bool]:
        """Get capacity information.

        Returns:
            Dict with active, max, and available connection counts

        """
        active = len(self.active_connections)
        return {
            "active": active,
            "max": self.maximum_connections,
            "available": self.maximum_connections - active,
            "at_capacity": active >= self.maximum_connections,
        }


__all__ = ["ConnectionRegistry"]
