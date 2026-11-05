"""WebSocket connection operations for test clients."""

from __future__ import annotations

import os
import json
from typing import TYPE_CHECKING, cast
import asyncio
import inspect
import contextlib
from urllib.parse import urlsplit, urlunsplit
from importlib.metadata import version

import websockets

from config.tests.defaults import DEFAULT_WEBSOCKET_PATH
from config.runtime.websocket import WEBSOCKET_PROTOCOL_VERSION

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager
    from collections.abc import Callable, Awaitable, AsyncGenerator

    from websockets.legacy.client import Connect

_HTTP_TO_WEBSOCKET = {"http": "ws", "https": "wss"}
WEBSOCKETS_HEADERS_VERSION = 13


def _normalize_path_scheme(url: str, default_path: str) -> tuple[str, str, str, str, str]:
    """Parse and normalize a WebSocket URL.

    Args:
        url: Address to connect to.
        default_path: Path of the default.

    Returns:
        And normalize a WebSocket URL.

    """
    parts = urlsplit(url)
    scheme = parts.scheme or "ws"
    netloc = parts.netloc
    path = parts.path or ""

    # Handle inputs like "localhost:8000" (missing scheme)
    if not netloc and parts.path and ":" in parts.path:
        netloc = parts.path
        path = ""

    scheme = _HTTP_TO_WEBSOCKET.get(scheme, scheme)

    normalized_path = path
    if not normalized_path or normalized_path.strip("/") == "":
        normalized_path = default_path if default_path.startswith("/") else f"/{default_path}"

    return scheme, netloc, normalized_path, parts.query, parts.fragment


def _choose_receive_method(websocket: object) -> Callable[[], str | Awaitable[str]]:
    """Support both `websockets` (recv) and Starlette/WebSocketTestClient (receive).

    Args:
        websocket: WebSocket connection of the client.

    Returns:
        The callable.

    Raises:
        TypeError: Websocket-like object must expose receive() or recv().

    """
    receiver = getattr(websocket, "receive", None)
    if not callable(receiver):
        receiver = getattr(websocket, "recv", None)
    if not callable(receiver):
        message = "websocket-like object must expose receive() or recv()"
        raise TypeError(message)
    return cast("Callable[[], str | Awaitable[str]]", receiver)


def read_api_key(
    api_key_variable: str = "API_KEY",
    default_key: str | None = None,
    *,
    api_key: str | None = None,
) -> str:
    """Read the configured API key.

    Args:
        api_key_variable: API key variable.
        default_key: Key of the default.
        api_key: Key of the API.

    Returns:
        The configured API key.

    Raises:
        ValueError: `api_key_variable` environment variable is required and must be set.

    """
    resolved_key = api_key or os.getenv(api_key_variable) or default_key
    if not resolved_key:
        message = f"{api_key_variable} environment variable is required and must be set"
        raise ValueError(message)
    return resolved_key


def build_websocket_url(
    url: str,
    api_key_variable: str = "API_KEY",
    default_key: str | None = None,
    *,
    api_key: str | None = None,
    default_path: str = DEFAULT_WEBSOCKET_PATH,
) -> str:
    """Normalize a WebSocket URL after validating API-key availability.

    Args:
        url: Address to connect to.
        api_key_variable: API key variable.
        default_key: Key of the default.
        api_key: Key of the API.
        default_path: Path of the default.

    Returns:
        The updated text.

    Raises:
        ValueError: Invalid WebSocket URL '`url`'. Expected format ws(s)://host[:port][`default_path`].

    """
    read_api_key(api_key_variable, default_key, api_key=api_key)

    scheme, netloc, path, query, fragment = _normalize_path_scheme(url, default_path)
    if not netloc:
        message = f"Invalid WebSocket URL '{url}'. Expected format ws(s)://host[:port][{default_path}]"
        raise ValueError(message)
    return urlunsplit((scheme, netloc, path, query, fragment))


def build_api_key_headers(
    api_key_variable: str = "API_KEY",
    default_key: str | None = None,
    *,
    api_key: str | None = None,
) -> dict[str, str]:
    """Build auth headers for websocket connections.

    Args:
        api_key_variable: API key variable.
        default_key: Key of the default.
        api_key: Key of the API.

    Returns:
        Auth headers for websocket connections.

    """
    resolved_key = read_api_key(api_key_variable, default_key, api_key=api_key)
    return {"X-API-Key": resolved_key}


async def send_end_frame(websocket: object) -> None:
    """Best-effort end signal to gracefully close the connection.

    Args:
        websocket: WebSocket connection of the client.

    """
    with contextlib.suppress(Exception):
        sender = getattr(websocket, "send", None)
        if not callable(sender):
            return
        result = sender(json.dumps({"type": "end", "v": WEBSOCKET_PROTOCOL_VERSION}))
        if inspect.isawaitable(result):
            await result


async def receive_raw_frame(
    websocket: object,
    *,
    receive_timeout_seconds: float | None = None,
) -> str:
    """Receive a single raw frame from a websocket-like object.

    Args:
        websocket: WebSocket connection of the client.
        receive_timeout_seconds: Receive timeout in seconds.

    Returns:
        The resulting text.

    """
    receiver = _choose_receive_method(websocket)
    receive_result = receiver()
    if inspect.isawaitable(receive_result):
        if receive_timeout_seconds is None:
            return await receive_result
        return await asyncio.wait_for(receive_result, receive_timeout_seconds)
    return receive_result


@contextlib.asynccontextmanager
async def open_websocket[ConnectionT](
    factory: Callable[[], AbstractAsyncContextManager[ConnectionT]],
    *,
    maximum_retries: int = 2,
    base_delay_seconds: float = 0.5,
    backoff_factor: float = 2.0,
) -> AsyncGenerator[ConnectionT, None]:
    """Attempt to open a websocket-like connection, retrying with exponential backoff.

    Retries `maximum_retries` times after the initial attempt, so the total
    attempts equal `maximum_retries + 1`. The `factory` must return a fresh async context
    manager each time (e.g., `lambda: websockets.connect(...)`).

    Args:
        factory: Function that creates the value.
        maximum_retries: Largest allowed retries.
        base_delay_seconds: Base delay in seconds.
        backoff_factor: Backoff factor.

    Yields:
        The next item from the stream.

    Raises:
        Exception: The operation fails with this error.

    """
    attempt = 0
    delay = base_delay_seconds
    while True:
        is_connected = False
        try:
            async with factory() as websocket:
                is_connected = True
                yield websocket
                return
        except Exception:
            if is_connected:
                raise
            if attempt >= maximum_retries:
                raise
            await asyncio.sleep(max(0.0, delay))
            delay *= backoff_factor
            attempt += 1


def connect_websocket(url: str, *, headers: dict[str, str] | None = None, **options: object) -> Connect:
    """Wrap websockets.connect with the header kwarg for the installed version.

    websockets <13 (older client) expects ``extra_headers``.
    websockets >=13 (new client) expects ``additional_headers``.

    Args:
        url: Address to connect to.
        headers: HTTP headers of the request.
        **options: Options.

    Returns:
        The updated value.

    """
    websockets_major_version = int(version("websockets").split(".")[0])
    header_parameter = (
        "extra_headers" if websockets_major_version < WEBSOCKETS_HEADERS_VERSION else "additional_headers"
    )
    connect = cast("Callable[..., Connect]", websockets.connect)
    return connect(url, **{header_parameter: headers or {}}, **options)


__all__ = [
    "build_api_key_headers",
    "build_websocket_url",
    "connect_websocket",
    "open_websocket",
    "read_api_key",
    "receive_raw_frame",
    "send_end_frame",
]
