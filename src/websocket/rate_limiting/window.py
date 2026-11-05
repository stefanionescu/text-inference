"""Simple sliding-window rate limiter helpers.

This module provides a time-based rate limiter using the sliding window
algorithm. It prevents abuse by limiting:

- Messages per connection per time window
- Cancel requests per time window

Sliding Window Algorithm:
    The limiter tracks timestamps of recent events in a deque. When a new
    event arrives:
    1. Remove timestamps older than (now - window_seconds)
    2. If remaining events >= limit, reject with a retry delay
    3. Otherwise, record the new timestamp and allow

This provides smoother rate limiting than fixed windows, as the limit
applies to any rolling window of the specified duration.

Example:
    limiter = SlidingWindowRateLimiter(limit=10, window_seconds=60)

    for message in messages:
        try:
            limiter.consume()
            process(message)
        except RateLimitError as error:
            await asyncio.sleep(error.retry_after_seconds)

"""

from __future__ import annotations

import time
import collections
from collections.abc import Callable

from src.errors import RateLimitError

# Type alias for injectable time functions (used in testing)
Clock = Callable[[], float]


class SlidingWindowRateLimiter:
    """Track events over a rolling window.

    This rate limiter uses a sliding window algorithm that provides smooth
    rate limiting without the "burst at window boundary" problem of fixed
    windows.

    The limiter can be disabled by setting limit=0 or window_seconds=0,
    in which case consume() always succeeds.

    Example:
        # Allow 25 messages per 60 seconds
        limiter = SlidingWindowRateLimiter(limit=25, window_seconds=60)

        try:
            limiter.consume()  # Record event
        except RateLimitError as error:
            print(f"Rate limited, retry in {error.retry_after_seconds:.1f}s")

    """

    def __init__(
        self,
        *,
        limit: int,
        window_seconds: float,
        clock: Clock | None = None,
    ) -> None:
        """Initialize a sliding-window limiter.

        Args:
            limit: Events allowed per window; zero or less disables the limiter.
            window_seconds: Window length in seconds; zero or less disables the limiter.
            clock: Function that returns the current time; None selects `time.monotonic`.

        """
        self.limit = max(0, int(limit))
        self.window_seconds = max(0.0, float(window_seconds))
        self._clock = clock or time.monotonic
        self._events: collections.deque[float] = collections.deque()
        self._is_enabled = self.limit > 0 and self.window_seconds > 0

    def consume(self) -> None:
        """Record an event or raise RateLimitError if the window is saturated.

        Call this method from one thread only, because it takes no lock around
        the event deque.

        Raises:
            RateLimitError: If the rate limit has been exceeded.

        """
        if not self._is_enabled:
            return

        current_time = self._clock()
        cutoff = current_time - self.window_seconds

        # Remove expired events from the front of the deque
        events = self._events
        while events and events[0] <= cutoff:
            events.popleft()

        # Reject the event when the window is at the limit
        if len(events) >= self.limit:
            # Calculate when the oldest event will expire
            retry_after_seconds = (events[0] + self.window_seconds) - current_time
            raise RateLimitError(
                retry_after_seconds=max(0.0, retry_after_seconds),
                limit=self.limit,
                window_seconds=self.window_seconds,
            )

        # Record this event
        events.append(current_time)


__all__ = ["RateLimitError", "SlidingWindowRateLimiter"]
