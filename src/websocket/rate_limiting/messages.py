"""Rate limiting utilities for WebSocket message handling.

This module provides rate limit selection and consumption for different
message types:

- Regular messages: Limited to prevent spam
- Cancel messages: Separate bucket to prevent cancel bursts starving messages
- Control messages (ping/pong/end): Exempt from rate limiting
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.websocket.transport import safe_send_flat
from config.runtime.websocket import WEBSOCKET_ERROR_RATE_LIMITED, WEBSOCKET_STATUS_RATE_LIMITED
from src.telemetry.instruments import get_metrics

from .window import RateLimitError, SlidingWindowRateLimiter

if TYPE_CHECKING:
    from fastapi import WebSocket


def select_rate_limiter(
    message_type: str,
    message_limiter: SlidingWindowRateLimiter,
    cancel_limiter: SlidingWindowRateLimiter,
) -> SlidingWindowRateLimiter | None:
    """Pick which limiter applies to the message type (if any)."""
    if message_type == "cancel":
        return cancel_limiter
    if message_type in {"ping", "pong", "end"}:
        return None
    return message_limiter


async def consume_limiter(
    websocket: WebSocket,
    limiter: SlidingWindowRateLimiter,
) -> bool:
    """Attempt to consume a limiter token, sending an error on failure."""
    try:
        limiter.consume()
    except RateLimitError:
        get_metrics().rate_limit_violations_total.add(1)
        await safe_send_flat(
            websocket,
            "error",
            status=WEBSOCKET_STATUS_RATE_LIMITED,
            code=WEBSOCKET_ERROR_RATE_LIMITED,
            message="Rate limit exceeded. Try again shortly.",
        )
        return False
    return True


__all__ = ["consume_limiter", "select_rate_limiter"]
