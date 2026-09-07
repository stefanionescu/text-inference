"""Input validation exceptions with structured error codes.

This module provides validation exceptions that carry both a human-readable
message and a machine-parseable error code for API responses.
"""


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


__all__ = ["ValidationError"]
