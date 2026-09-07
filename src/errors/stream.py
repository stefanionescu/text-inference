"""Streaming and cancellation exceptions.

This module provides exceptions used during streaming generation
to signal cooperative cancellation.
"""


class StreamCancelledError(Exception):
    """Raised when a cooperative cancel check requests termination.

    This exception is used for clean stream termination when the
    cancel_check callback returns True. It allows callers to
    distinguish cancellation from other errors.
    """


__all__ = ["StreamCancelledError"]
