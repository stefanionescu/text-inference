"""Logging context helpers for consistent structured fields."""

from __future__ import annotations

import os
import logging
import contextlib
from dataclasses import dataclass
from contextvars import ContextVar, Token
from config.runtime.logging import APPLICATION_LOG_DATE_FORMAT, APPLICATION_LOG_FORMAT, APPLICATION_LOG_LEVEL

_SESSION_ID: ContextVar[str] = ContextVar("session_id", default="-")
_REQUEST_ID: ContextVar[str] = ContextVar("request_id", default="-")
_CLIENT_ID: ContextVar[str] = ContextVar("client_id", default="-")


@dataclass(frozen=True)
class LogContext:
    """Current structured logging context values."""

    session_id: str
    request_id: str
    client_id: str


@dataclass(slots=True)
class _LoggingState:
    """Process-wide logging installation state."""

    is_context_installed: bool = False


_LOGGING_STATE = _LoggingState()


def set_log_context(
    *,
    session_id: str | None = None,
    request_id: str | None = None,
    client_id: str | None = None,
) -> list[tuple[ContextVar[str], Token[str]]]:
    """Set log context values and return tokens for reset."""
    tokens: list[tuple[ContextVar[str], Token[str]]] = []
    if session_id is not None:
        tokens.append((_SESSION_ID, _SESSION_ID.set(session_id)))
    if request_id is not None:
        tokens.append((_REQUEST_ID, _REQUEST_ID.set(request_id)))
    if client_id is not None:
        tokens.append((_CLIENT_ID, _CLIENT_ID.set(client_id)))
    return tokens


def current_log_context() -> LogContext:
    """Return the current structured logging context snapshot."""
    session_id = _SESSION_ID.get()
    request_id = _REQUEST_ID.get()
    client_id = _CLIENT_ID.get()
    return LogContext(session_id=session_id, request_id=request_id, client_id=client_id)


def _configure_log_record_factory() -> None:
    """Install a LogRecord factory that injects context fields."""
    if _LOGGING_STATE.is_context_installed:
        return

    previous_factory = logging.getLogRecordFactory()

    def record_factory(*arguments: object, **keyword_arguments: object) -> logging.LogRecord:
        """Create a log record with current context fields attached."""
        record = previous_factory(*arguments, **keyword_arguments)
        record.session_id = _SESSION_ID.get()
        record.request_id = _REQUEST_ID.get()
        record.client_id = _CLIENT_ID.get()
        return record

    logging.setLogRecordFactory(record_factory)
    _LOGGING_STATE.is_context_installed = True


def configure_logging() -> None:
    """Initialize root logging configuration once per process."""
    _configure_log_record_factory()
    log_level = (
        os.environ.get("APPLICATION_LOG_LEVEL", APPLICATION_LOG_LEVEL).strip() or APPLICATION_LOG_LEVEL
    ).upper()
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        logging.basicConfig(
            level=log_level,
            format=APPLICATION_LOG_FORMAT,
            datefmt=APPLICATION_LOG_DATE_FORMAT,
        )
    else:
        root_logger.setLevel(log_level)
        for log_handler in root_logger.handlers:
            with contextlib.suppress(TypeError, ValueError):
                log_handler.setLevel(log_level)
                log_handler.setFormatter(
                    logging.Formatter(APPLICATION_LOG_FORMAT, datefmt=APPLICATION_LOG_DATE_FORMAT),
                )

    logging.getLogger("src").setLevel(log_level)


__all__ = [
    "LogContext",
    "configure_logging",
    "current_log_context",
    "set_log_context",
]
