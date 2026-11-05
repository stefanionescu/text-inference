"""Per-connection WebSocket lifecycle helpers (idle enforcement).

This module implements idle timeout enforcement for WebSocket connections.
Each connection gets a WebSocketLifecycle instance that:

1. Tracks last activity timestamp (updated via touch())
2. Runs a background watchdog task that checks for idleness
3. Closes the connection automatically when idle timeout is reached

This prevents resource exhaustion from abandoned connections (e.g., client
crashed, network dropped) that would otherwise stay open indefinitely.

The watchdog runs periodically (WEBSOCKET_WATCHDOG_TICK_SECONDS) and compares
the last activity time against the idle timeout (WEBSOCKET_IDLE_TIMEOUT_SECONDS).

Usage:
    lifecycle = WebSocketLifecycle(websocket, idle_timeout_seconds=150.0, watchdog_tick_seconds=10.0)
    lifecycle.start()  # Start watchdog

    # In receiver:
    lifecycle.touch()  # Reset idle timer

    # On cleanup:
    await lifecycle.stop()
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING
import asyncio
import logging
import contextlib

from src.telemetry.sentry import add_breadcrumb
from config.runtime.websocket import WEBSOCKET_CLOSE_IDLE_CODE, WEBSOCKET_CLOSE_IDLE_REASON
from src.telemetry.instruments import get_metrics

if TYPE_CHECKING:
    from fastapi import WebSocket

logger = logging.getLogger(__name__)


class WebSocketLifecycle:
    """Tracks activity timestamps and enforces idle timeouts.

    This class manages the lifecycle of a single WebSocket connection,
    specifically handling idle timeout detection and enforcement.

    """

    def __init__(
        self,
        websocket: WebSocket,
        idle_timeout_seconds: float,
        watchdog_tick_seconds: float,
        idle_close_code: int | None = None,
    ) -> None:
        """Initialize lifecycle timers for one WebSocket.

        Args:
            websocket: WebSocket connection of the client.
            idle_timeout_seconds: Idle timeout in seconds.
            watchdog_tick_seconds: Watchdog tick in seconds.
            idle_close_code: Code of the idle close.

        """
        self._websocket = websocket
        self._idle_timeout_seconds = float(idle_timeout_seconds)
        self._watchdog_tick_seconds = float(watchdog_tick_seconds)
        self._idle_close_code = idle_close_code if idle_close_code is not None else WEBSOCKET_CLOSE_IDLE_CODE
        self._idle_close_reason = WEBSOCKET_CLOSE_IDLE_REASON
        self._last_activity_time = time.monotonic()
        self._watchdog_stop_event = asyncio.Event()  # Signals watchdog to stop
        self._idle_timeout_event = asyncio.Event()
        self._watchdog_task: asyncio.Task[None] | None = None  # Watchdog task reference

    def touch(self) -> None:
        """Record recent activity (resets idle countdown)."""
        previous_activity = self._last_activity_time
        self._last_activity_time = time.monotonic()
        if self._last_activity_time < previous_activity:
            logger.debug("monotonic clock moved backward while touching websocket lifecycle")

    def has_idle_timed_out(self) -> bool:
        """Check whether the watchdog has fired an idle timeout close.

        Returns:
            Whether the watchdog has fired an idle timeout close.

        """
        has_timed_out = self._idle_timeout_event.is_set()
        if has_timed_out:
            self._watchdog_stop_event.set()
        return has_timed_out

    def start(self) -> asyncio.Task[None]:
        """Start the watchdog task (idempotent).

        Returns:
            The task.

        """
        task = self._watchdog_task
        if task is None:
            self._watchdog_task = asyncio.create_task(self._watchdog_loop())
            task = self._watchdog_task
        return task

    async def stop(self) -> None:
        """Stop the watchdog task and wait for it to finish."""
        self._watchdog_stop_event.set()
        if self._watchdog_task is None:
            return
        self._watchdog_task.cancel()
        with contextlib.suppress(asyncio.CancelledError, OSError, RuntimeError):
            await self._watchdog_task
        self._watchdog_task = None

    async def _watchdog_loop(self) -> None:
        """Background loop that periodically checks for idle connections.

        Runs until stopped or idle timeout is reached. Closes the WebSocket
        with an appropriate code when idle timeout expires.

        Raises:
            asyncio.CancelledError: The task was cancelled.

        """
        watchdog_tick_seconds = self._watchdog_tick_seconds
        try:
            while not self._watchdog_stop_event.is_set():
                await asyncio.sleep(watchdog_tick_seconds)
                if self._watchdog_stop_event.is_set():
                    break
                # Check if connection has been idle too long
                if (time.monotonic() - self._last_activity_time) >= self._idle_timeout_seconds:
                    get_metrics().timeout_disconnects_total.add(1)
                    add_breadcrumb("Idle timeout", category="lifecycle")
                    logger.info("WebSocket idle timeout reached; closing connection")
                    self._idle_timeout_event.set()
                    self._watchdog_stop_event.set()  # Signal handler to exit
                    await self._close_websocket()
                    break
        except asyncio.CancelledError:
            raise  # Normal shutdown path; propagate task cancellation cleanly
        except (OSError, RuntimeError, ValueError):
            logger.debug("Idle watchdog exiting due to unexpected error", exc_info=True)

    async def _close_websocket(self) -> None:
        """Close the WebSocket with idle timeout code/reason."""
        websocket = self._websocket
        close_code = self._idle_close_code
        close_reason = self._idle_close_reason
        with contextlib.suppress(OSError, RuntimeError, ValueError):
            await websocket.close(code=close_code, reason=close_reason)


__all__ = ["WebSocketLifecycle"]
