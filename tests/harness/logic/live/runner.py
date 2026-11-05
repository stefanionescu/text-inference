"""Interactive live session orchestration."""

from __future__ import annotations

import uuid
import logging
from dataclasses import dataclass

import websockets

from tests.state import LiveSession, PromptProfile
from config.tests.defaults import WEBSOCKET_IDLE_CLOSE_CODE
from tests.harness.client.errors import ServerError, IdleTimeoutError, ConnectionClosedError
from tests.harness.client.websocket import open_websocket, connect_websocket, build_websocket_url, build_api_key_headers
from tests.harness.reporting.terminal import dim, write_line, section_header
from tests.harness.environment.settings import (
    DEFAULT_PING_TIMEOUT_SECONDS,
    DEFAULT_PING_INTERVAL_SECONDS,
)

from .cli import run_interactive_loop
from .client import LiveClient
from .commands import print_help
from .profiles import PromptProfileRegistry

logger = logging.getLogger("live")


@dataclass(frozen=True)
class LiveRunRequest:
    """Inputs for an interactive live session.

    Attributes:
        server_url: Server URL.
        api_key: Key of the API.
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        timeout_seconds: Timeout in seconds.
        sampling: Sampling overrides of the request.
        message: Message to send, check, or report.

    """

    server_url: str
    api_key: str | None
    gender: str
    personality: str
    timeout_seconds: float
    sampling: dict[str, float | int | bool] | None
    message: list[str] | None


@dataclass(frozen=True)
class LiveConnection:
    """Resolved WebSocket inputs for a live session.

    Attributes:
        server_url: Server URL.
        authentication_headers: Authentication headers.
        session: Session to use.
        timeout_seconds: Timeout in seconds.
        registry: Registry of prompt profiles.
        initial_message: Initial message.

    """

    server_url: str
    authentication_headers: dict[str, str]
    session: LiveSession
    timeout_seconds: float
    registry: PromptProfileRegistry
    initial_message: str


def _prepare_session(
    registry: PromptProfileRegistry,
    gender: str,
    personality: str,
    *,
    message: list[str] | None,
    sampling: dict[str, float | int | bool] | None,
) -> tuple[LiveSession, PromptProfile, str]:
    """Resolve the selected prompt profile and initial message.

    Args:
        registry: Registry of prompt profiles.
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        message: Message to send, check, or report.
        sampling: Sampling overrides of the request.

    Returns:
        The selected prompt profile and initial message.

    """
    profile = registry.require_profile(gender, personality)
    initial_message = " ".join(message).strip() if message else "Hey!"
    session = LiveSession(
        session_id=f"live-{uuid.uuid4()}",
        profile=profile,
        sampling=sampling,
    )
    return session, profile, initial_message


def _print_banner(server_url: str, profile: PromptProfile) -> None:
    """Print the selected connection and prompt profile.

    Args:
        server_url: Server URL.
        profile: Prompt profile to use.

    """
    write_line(f"\n{section_header('LIVE SESSION')}")
    write_line(dim(f"  server: {server_url}"))
    write_line(dim(f"  profile: {profile.gender}/{profile.personality}"))
    print_help(profile.gender, profile.personality)


async def _run_session(connection: LiveConnection) -> None:
    """Connect and run the interactive input loop.

    Args:
        connection: Open connection to the server.

    """
    async with open_websocket(
        lambda: connect_websocket(
            connection.server_url,
            headers=connection.authentication_headers,
            max_queue=None,
            ping_interval=DEFAULT_PING_INTERVAL_SECONDS,
            ping_timeout=DEFAULT_PING_TIMEOUT_SECONDS,
        ),
    ) as websocket:
        client = LiveClient(websocket, connection.session, connection.timeout_seconds)
        try:
            await client.send_user_message(connection.initial_message)
            await run_interactive_loop(client, connection.registry, is_banner_shown=False)
        finally:
            await client.close()


def _log_websocket_close(exception: Exception) -> None:
    """Report an expected idle close or another remote close.

    Args:
        exception: Exception to inspect.

    """
    close_code = getattr(exception, "code", None)
    close_reason = getattr(exception, "reason", None)
    if close_code == WEBSOCKET_IDLE_CLOSE_CODE or (close_reason and "idle" in str(close_reason).lower()):
        logger.info("Session ended due to inactivity. Goodbye!")
    else:
        logger.warning("Server closed the connection (code=%s). Exiting.", close_code)


def _raise_for_server_error(exception: ServerError) -> None:
    """Translate terminal server errors into live-client exits.

    Args:
        exception: Exception to inspect.

    Raises:
        SystemExit: The command stops because of an error.

    """
    if exception.error_code == "authentication_failed":
        logger.error("Authentication failed. Check --api-key or API_KEY.")
        raise SystemExit(1) from exception
    if exception.error_code == "server_at_capacity":
        logger.error("Server is busy. Please try again later.")
        raise SystemExit(1) from exception
    logger.error("Server error: %s", exception)
    raise SystemExit(1) from exception


async def run_live_session(request: LiveRunRequest) -> None:
    """Run the interactive live session.

    Args:
        request: Request to run.

    Raises:
        SystemExit: The command stops because of an error.

    """
    registry = PromptProfileRegistry()
    try:
        session, profile, initial_message = _prepare_session(
            registry,
            request.gender,
            request.personality,
            message=request.message,
            sampling=request.sampling,
        )
    except ValueError as exception:
        raise SystemExit(str(exception)) from exception

    _print_banner(request.server_url, profile)
    connection = LiveConnection(
        server_url=build_websocket_url(request.server_url, api_key=request.api_key),
        authentication_headers=build_api_key_headers(api_key=request.api_key),
        session=session,
        timeout_seconds=request.timeout_seconds,
        registry=registry,
        initial_message=initial_message,
    )
    try:
        await _run_session(connection)
    except TimeoutError:
        logger.exception("Transaction timed out while connected to %s", request.server_url)
        raise SystemExit(1) from None
    except (websockets.ConnectionClosedError, websockets.ConnectionClosedOK) as exception:
        _log_websocket_close(exception)
    except IdleTimeoutError:
        logger.info("Session ended due to inactivity. Goodbye!")
    except ServerError as exception:
        _raise_for_server_error(exception)
    except ConnectionClosedError as exception:
        logger.warning("Connection closed: %s", exception)
    except (OSError, RuntimeError, ValueError, websockets.WebSocketException):
        logger.exception("Unexpected error while running live client")


__all__ = ["LiveRunRequest", "run_live_session"]
