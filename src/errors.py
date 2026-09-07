"""Application validation, cancellation, and rate-limit errors."""


class ValidationError(Exception):
    """Structured validation failure with error code metadata.

    This exception is raised when input validation fails. It carries
    both an error_code (for programmatic handling) and a message
    (for human-readable error responses).

    Attributes:
        error_code: Machine-parseable error identifier.
        message: Human-readable error description.

    """

    def __init__(self, error_code: str, message: str) -> None:
        """Initialize validation error details."""
        super().__init__(message)
        self.error_code = error_code
        self.message = message


class StreamCancelledError(Exception):
    """Raised when a cooperative cancel check requests termination.

    This exception is used for clean stream termination when the
    cancel_check callback returns True. It allows callers to
    distinguish cancellation from other errors.
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


__all__ = ["RateLimitError", "StreamCancelledError", "ValidationError"]
