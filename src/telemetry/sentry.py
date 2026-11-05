"""Sentry error tracking with per-class rate-limiting."""

from __future__ import annotations

import time
from logging import getLogger
from dataclasses import field, dataclass

import sentry_sdk

from src.logs.context import current_log_context
from src.runtime.environment import read_environment_text, read_environment_float
from config.runtime.telemetry import (
    SENTRY_DSN,
    SENTRY_RELEASE,
    SENTRY_ENVIRONMENT,
    SENTRY_SAMPLE_RATE,
    SENTRY_TAG_CLIENT_ID,
    SENTRY_TAG_REQUEST_ID,
    SENTRY_TAG_SESSION_ID,
    SENTRY_RATE_LIMIT_SECONDS,
)

logger = getLogger(__name__)


@dataclass(slots=True)
class _SentryState:
    """Process-wide Sentry lifecycle and rate-limit state.

    Attributes:
        is_initialized: Whether it is initialized.
        error_timestamps: Error timestamps.

    """

    is_initialized: bool = False
    error_timestamps: dict[str, float] = field(default_factory=dict)


_SENTRY_STATE = _SentryState()


def initialize_sentry() -> None:
    """Initialize Sentry SDK. Idempotent."""
    if _SENTRY_STATE.is_initialized:
        return
    sentry_dsn = read_environment_text("SENTRY_DSN", SENTRY_DSN)
    if not sentry_dsn:
        logger.info("Sentry disabled (SENTRY_DSN not set)")
        return

    environment = read_environment_text("SENTRY_ENVIRONMENT", SENTRY_ENVIRONMENT)
    release = read_environment_text("SENTRY_RELEASE", SENTRY_RELEASE)
    sample_rate = min(1.0, max(0.0, read_environment_float("SENTRY_SAMPLE_RATE", SENTRY_SAMPLE_RATE)))
    sentry_sdk.init(
        dsn=sentry_dsn,
        environment=environment,
        release=release or None,
        traces_sample_rate=0.0,
        sample_rate=sample_rate,
        attach_stacktrace=True,
    )

    _SENTRY_STATE.is_initialized = True
    logger.info("Sentry initialized: environment=%s", environment)


def shutdown_sentry() -> None:
    """Flush Sentry events. Idempotent."""
    if not _SENTRY_STATE.is_initialized:
        return
    try:
        sentry_sdk.flush(timeout=2.0)
    except (OSError, RuntimeError):
        logger.debug("failed to flush Sentry during shutdown", exc_info=True)
    _SENTRY_STATE.is_initialized = False


def capture_error(
    error: BaseException,
    *,
    session_id: str | None = None,
    request_id: str | None = None,
    client_id: str | None = None,
    extra: dict[str, object] | None = None,
) -> None:
    """Report an error to Sentry with rate-limiting per error class.

    Args:
        error: Error text or error object to report.
        session_id: ID of the session.
        request_id: ID of the request.
        client_id: ID of the client.
        extra: Extra fields to include.

    """
    if not _SENTRY_STATE.is_initialized:
        return

    key = type(error).__qualname__
    now = time.monotonic()
    last = _SENTRY_STATE.error_timestamps.get(key, 0.0)
    if (now - last) < SENTRY_RATE_LIMIT_SECONDS:
        return
    _SENTRY_STATE.error_timestamps[key] = now

    log_context = current_log_context()
    active_session_id = session_id or log_context.session_id
    active_request_id = request_id or log_context.request_id
    active_client_id = client_id or log_context.client_id

    with sentry_sdk.push_scope() as scope:
        scope.set_tag(SENTRY_TAG_SESSION_ID, active_session_id)
        scope.set_tag(SENTRY_TAG_REQUEST_ID, active_request_id)
        scope.set_tag(SENTRY_TAG_CLIENT_ID, active_client_id)
        if extra:
            for key, value in extra.items():
                scope.set_extra(key, value)
        sentry_sdk.capture_exception(error)


def add_breadcrumb(
    message: str,
    *,
    category: str,
    level: str = "metadata",
    payload: dict[str, object] | None = None,
) -> None:
    """Add a Sentry breadcrumb. No-op when Sentry is disabled.

    Args:
        message: Message to send, check, or report.
        category: Category label of the record.
        level: Logging level name.
        payload: Decoded message fields.

    """
    if not _SENTRY_STATE.is_initialized:
        return
    sentry_sdk.add_breadcrumb(message=message, category=category, level=level, payload=payload or {})


__all__ = ["add_breadcrumb", "capture_error", "initialize_sentry", "shutdown_sentry"]
