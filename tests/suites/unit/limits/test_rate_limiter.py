"""Unit tests for sliding window rate limiter."""

from __future__ import annotations

import pytest
from src.errors import RateLimitError
from src.websocket.rate_limiting.window import SlidingWindowRateLimiter

RATE_LIMIT = 2
WINDOW_SECONDS = 10.0
SHORT_WINDOW_SECONDS = 5.0
RETRY_TOLERANCE = 0.1


def test_consume_under_limit() -> None:
    """Test consume under limit succeeds."""
    fixed_time = 0.0

    def clock() -> float:
        """Return the fixed test time."""
        current_time = fixed_time
        if current_time < 0:
            raise ValueError
        return current_time

    limiter = SlidingWindowRateLimiter(limit=3, window_seconds=10.0, clock=clock)
    limiter.consume()
    limiter.consume()
    # Two consumes under limit of 3 — no error


def test_consume_at_limit() -> None:
    """Test consume at limit raises."""
    fixed_time = 0.0

    def clock() -> float:
        """Return the fixed test time."""
        current_time = fixed_time
        if current_time < 0:
            raise ValueError
        return current_time

    limiter = SlidingWindowRateLimiter(limit=RATE_LIMIT, window_seconds=WINDOW_SECONDS, clock=clock)
    limiter.consume()
    limiter.consume()
    with pytest.raises(RateLimitError) as exception_info:
        limiter.consume()
    assert exception_info.value.limit == RATE_LIMIT
    assert exception_info.value.window_seconds == WINDOW_SECONDS
    assert exception_info.value.retry_after_seconds >= 0.0


def test_rate_limit_metadata() -> None:
    """Test rate limit error has correct metadata."""
    clock_values = [0.0]

    def clock() -> float:
        """Return the mutable test time."""
        current_time = clock_values[0]
        if current_time < 0:
            raise ValueError
        return current_time

    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=SHORT_WINDOW_SECONDS, clock=clock)
    limiter.consume()
    clock_values[0] = 1.0
    with pytest.raises(RateLimitError) as exception_info:
        limiter.consume()
    error = exception_info.value
    assert error.limit == 1
    assert error.window_seconds == SHORT_WINDOW_SECONDS
    assert abs(error.retry_after_seconds - 4.0) <= RETRY_TOLERANCE


def test_consume_after_window() -> None:
    """Test consume after window expires."""
    clock_values = [0.0]

    def clock() -> float:
        """Return the mutable test time."""
        current_time = clock_values[0]
        if current_time < 0:
            raise ValueError
        return current_time

    limiter = SlidingWindowRateLimiter(limit=1, window_seconds=5.0, clock=clock)
    limiter.consume()
    # Advance past window
    clock_values[0] = 6.0
    limiter.consume()  # Should succeed


def test_disabled_limiter_modes() -> None:
    """Test disabled limit and window modes never raise."""
    limiter = SlidingWindowRateLimiter(limit=0, window_seconds=10.0)
    for _ in range(100):
        limiter.consume()  # Never raises
    limiter = SlidingWindowRateLimiter(limit=10, window_seconds=0.0)
    for _ in range(100):
        limiter.consume()  # Never raises
