"""Rate limiting exception with retry metadata.

This module provides the RateLimitError exception that carries information
about when a client can retry after being rate limited.
"""


class RateLimitError(Exception):
    """Raised when a rate limiter rejects an action.

    This exception provides information about when the client can retry
    and the limit that was exceeded.

    Attributes:
        retry_after_seconds: Seconds until a new slot becomes available.
        limit: The maximum allowed events per window.
        window_seconds: The duration of the rate limit window.

    """

    def __init__(
        self,
        *,
        retry_after_seconds: float,
        limit: int,
        window_seconds: float,
        message: str | None = None,
    ) -> None:
        """Initialize rate-limit retry metadata."""
        super().__init__(message or "rate limit exceeded")
        self.retry_after_seconds = max(0.0, float(retry_after_seconds))
        self.limit = max(0, int(limit))
        self.window_seconds = max(0.0, float(window_seconds))


__all__ = ["RateLimitError"]
