"""Client-side pacing helpers mirroring server rolling windows."""

from __future__ import annotations

import time
import asyncio
import collections
from collections import deque


class SlidingWindowPacer:
    """Asynchronous pacer that enforces a rolling window cap."""

    def __init__(self, limit: int, window_seconds: float) -> None:
        """Initialize the pacer with a maximum event count and window.

        Args:
            limit: Largest number to allow.
            window_seconds: Window in seconds.

        """
        self.limit = max(0, int(limit))
        self.window_seconds = max(0.0, float(window_seconds))
        self._events: deque[float] = collections.deque()

    @property
    def is_enabled(self) -> bool:
        """Return whether pacing is active."""
        return self.limit > 0 and self.window_seconds > 0

    async def wait_turn(self) -> None:
        """Sleep just enough so the next event fits inside the window."""
        if not self.is_enabled:
            return

        while True:
            current_time = time.monotonic()
            self._trim(current_time)
            if len(self._events) < self.limit:
                self._events.append(current_time)
                return

            # Window is saturated; wait for the oldest event to expire.
            earliest = self._events[0]
            sleep_seconds = (earliest + self.window_seconds) - current_time
            if sleep_seconds > 0:
                await asyncio.sleep(sleep_seconds)
            else:
                # The oldest event has expired; drop it and loop.
                self._events.popleft()

    def _trim(self, current_time: float) -> None:
        cutoff = current_time - self.window_seconds
        events = self._events
        while events and events[0] <= cutoff:
            events.popleft()


__all__ = ["SlidingWindowPacer"]
