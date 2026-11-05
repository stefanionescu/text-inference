"""API-key authentication and failure throttling."""

from __future__ import annotations

import hmac
import time
from typing import TYPE_CHECKING
import logging
from collections import deque
from dataclasses import dataclass

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import WebSocket

    from src.runtime.config import WebSocketSettings, AuthenticationSettings

logger = logging.getLogger(__name__)

# API Key can be provided via explicit header or Authorization bearer token.
_AUTHENTICATION_FAILURES: dict[str, deque[float]] = {}


@dataclass(frozen=True, slots=True)
class AuthenticationPolicy:
    """Authentication settings and mutable failure tracking."""

    authentication_settings: AuthenticationSettings
    websocket_settings: WebSocketSettings
    authentication_failures: dict[str, deque[float]]
    clock: Callable[[], float] = time.monotonic


def build_authentication_policy(
    *,
    authentication_settings: AuthenticationSettings,
    websocket_settings: WebSocketSettings,
    authentication_failures: dict[str, deque[float]] | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> AuthenticationPolicy:
    """Build an auth policy, defaulting to the shared failure store."""
    failures = _AUTHENTICATION_FAILURES if authentication_failures is None else authentication_failures
    return AuthenticationPolicy(
        authentication_settings=authentication_settings,
        websocket_settings=websocket_settings,
        authentication_failures=failures,
        clock=clock,
    )


def _extract_bearer_key(value: str | None) -> str | None:
    """Extract bearer token value from an Authorization header."""
    if not value:
        return None
    prefix = "bearer "
    normalized = value.strip()
    if len(normalized) <= len(prefix) or normalized[: len(prefix)].lower() != prefix:
        return None
    token = normalized[len(prefix) :].strip()
    return token or None


def _select_api_key(*candidates: str | None) -> str | None:
    """Return the first non-empty API key candidate from the provided values."""
    candidate_values = candidates
    for candidate in candidate_values:
        if candidate:
            return candidate
    return None


def _validate_candidate(
    provided_key: str | None,
    *,
    context: str,
    authentication_settings: AuthenticationSettings,
) -> tuple[bool, str | None, str]:
    """Validate a candidate API key and return (is_valid, key, error_code)."""
    if not provided_key:
        logger.warning("%s missing API key", context)
        return False, None, "missing"
    if not validate_api_key(provided_key, configured_api_key=authentication_settings.api_key):
        logger.warning("%s invalid API key", context)
        return False, None, "invalid"
    return True, provided_key, ""


def _client_failure_key(client_host: str | None) -> str:
    """Return a stable auth failure key for a client host."""
    raw_host = client_host or "unknown"
    stripped_host = raw_host.strip()
    return stripped_host or "unknown"


def _prune_failures(
    client_key: str,
    current_time: float,
    *,
    websocket_settings: WebSocketSettings,
    authentication_failures: dict[str, deque[float]],
) -> deque[float]:
    """Drop expired auth failures and return the active window."""
    entries = authentication_failures.setdefault(client_key, deque())
    cutoff = current_time - websocket_settings.rate_limit_window_seconds
    while entries and entries[0] <= cutoff:
        entries.popleft()
    return entries


def _is_authentication_throttled(
    client_key: str,
    *,
    websocket_settings: WebSocketSettings,
    authentication_failures: dict[str, deque[float]],
    clock: Callable[[], float],
) -> bool:
    """Return whether a client has exceeded auth failure limits."""
    current_time = clock()
    entries = _prune_failures(
        client_key, current_time, websocket_settings=websocket_settings, authentication_failures=authentication_failures
    )
    return len(entries) >= websocket_settings.authentication_failures_per_window


def _record_authentication_failure(
    client_key: str,
    *,
    websocket_settings: WebSocketSettings,
    authentication_failures: dict[str, deque[float]],
    clock: Callable[[], float],
) -> None:
    """Record one authentication failure for a client."""
    current_time = clock()
    entries = _prune_failures(
        client_key, current_time, websocket_settings=websocket_settings, authentication_failures=authentication_failures
    )
    entries.append(current_time)


def _clear_authentication_failures(client_key: str, *, authentication_failures: dict[str, deque[float]]) -> None:
    """Clear recorded authentication failures for a client."""
    failures = authentication_failures
    if client_key in failures:
        failures.pop(client_key, None)


def _websocket_client_key(websocket: WebSocket) -> str:
    """Return the auth failure key for a WebSocket request."""
    client = websocket.client
    host = client.host if client else None
    return _client_failure_key(host)


def validate_api_key(
    provided_key: str,
    *,
    configured_api_key: str | None,
) -> bool:
    """Validate provided API key against configured key.

    Args:
        provided_key: The API key to validate
        configured_api_key: The configured server-side API key.

    Returns:
        True if valid, False otherwise

    """
    expected_key = configured_api_key
    if not expected_key:
        return False
    return hmac.compare_digest(provided_key, expected_key)


async def authenticate_websocket(
    websocket: WebSocket,
    *,
    policy: AuthenticationPolicy,
) -> bool:
    """Authenticate WebSocket connection using API key.

    Args:
        websocket: WebSocket connection to authenticate
        policy: Authentication settings, rate limits, failure store, and clock.

    Returns:
        True if authenticated, False otherwise

    """
    client_key = _websocket_client_key(websocket)
    if _is_authentication_throttled(
        client_key,
        websocket_settings=policy.websocket_settings,
        authentication_failures=policy.authentication_failures,
        clock=policy.clock,
    ):
        logger.warning("WebSocket authentication throttled client=%s", client_key)
        return False

    provided_key = _select_api_key(
        websocket.headers.get("x-api-key"),
        _extract_bearer_key(websocket.headers.get("authorization")),
    )
    is_valid, _, _error_code = _validate_candidate(
        provided_key,
        context="WebSocket connection",
        authentication_settings=policy.authentication_settings,
    )
    if not is_valid:
        _record_authentication_failure(
            client_key,
            websocket_settings=policy.websocket_settings,
            authentication_failures=policy.authentication_failures,
            clock=policy.clock,
        )
        return False
    _clear_authentication_failures(client_key, authentication_failures=policy.authentication_failures)
    logger.info("WebSocket connection authenticated successfully")
    return True


__all__ = [
    "AuthenticationPolicy",
    "authenticate_websocket",
    "build_authentication_policy",
    "validate_api_key",
]
