"""Server-originated error root."""

from __future__ import annotations

from .client import TestClientError
from typing import TYPE_CHECKING, ClassVar

if TYPE_CHECKING:
    from collections.abc import Callable


class ServerError(TestClientError):
    """Raised when the server returns an error message."""

    _SUBCLASS_MAP: ClassVar[dict[str, type[ServerError]]] = {}
    _is_recoverable: ClassVar[bool] = False
    user_message: ClassVar[str] = ""

    def __init__(
        self,
        error_code: str,
        message: str,
        *,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Initialize a server error."""
        self.error_code = error_code
        self.message = message
        self.extra = extra or {}
        super().__init__(f"{error_code}: {message}")

    @classmethod
    def from_message(cls, payload: dict[str, object]) -> ServerError:
        """Create an appropriate ServerError subclass from a server error message."""
        raw_error_code = payload.get("code") or payload.get("error_code") or "unknown"
        error_code = raw_error_code if isinstance(raw_error_code, str) else str(raw_error_code)
        raw_message = payload.get("message")
        error_message = raw_message if isinstance(raw_message, str) else str(payload)
        extra = {
            key: value
            for key, value in payload.items()
            if key not in ("type", "error_code", "code", "message", "status")
        }
        error_class = cls._SUBCLASS_MAP.get(error_code, ServerError)
        return error_class(error_code, error_message, extra=extra)

    @classmethod
    def register_codes(cls, codes: tuple[str, ...], error_class: type[ServerError]) -> None:
        """Register an error class for server error codes."""
        for code in codes:
            cls._SUBCLASS_MAP[code] = error_class

    @property
    def retry_after_seconds(self) -> int | None:
        """Return retry delay seconds when provided by the server."""
        value = self.extra.get("retry_in")
        if isinstance(value, int):
            return value
        return None

    @property
    def friendly_message(self) -> str | None:
        """Return a user-facing message when provided by the server."""
        value = self.extra.get("friendly_message")
        if isinstance(value, str):
            return value
        return None

    def is_recoverable(self) -> bool:
        """Return whether the client may retry after this error."""
        return self._is_recoverable

    def format_for_user(self) -> str:
        """Format the error for terminal output."""
        friendly_message = self.friendly_message
        if friendly_message:
            return friendly_message
        if self.user_message:
            return self.user_message
        return self.message


def _register_error_code[ErrorT: type[ServerError]](*codes: str) -> Callable[[ErrorT], ErrorT]:
    """Register error codes with their exception class."""

    def decorator(cls: ErrorT) -> ErrorT:
        registered_cls = cls
        ServerError.register_codes(codes, registered_cls)
        return registered_cls

    return decorator


__all__ = ["ServerError", "_register_error_code"]
