"""Rate limit server error type."""

from __future__ import annotations

from .server import ServerError, _register_error_code


@_register_error_code("rate_limited", "message_rate_limited", "cancel_rate_limited")
class RateLimitError(ServerError):
    """Raised when rate limits are exceeded."""

    _is_recoverable = True

    def format_for_user(self) -> str:
        """Format the rate limit failure for terminal output."""
        if self.friendly_message:
            return self.friendly_message
        retry_delay_seconds = self.retry_after_seconds
        if retry_delay_seconds:
            return f"Rate limited. Please wait {retry_delay_seconds} second(s) before sending another message."
        return "Rate limited. Please slow down."


__all__ = ["RateLimitError"]
