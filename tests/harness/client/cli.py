"""CLI argument helpers for test utilities.

This module provides reusable argparse argument groups shared by all test
scripts. It includes connection arguments (server URL and API key) and sampling
override arguments (temperature, top_p, and related values).
"""

from __future__ import annotations

import os
import sys
from typing import TYPE_CHECKING, Any
import asyncio
import argparse
from collections.abc import Mapping

from config.tests.defaults import TRANSACTION_TIMEOUT_SECONDS
from config.prompt.sampling import (
    TOP_K,
    TOP_P,
    TEMPERATURE,
    PRESENCE_PENALTY,
    FREQUENCY_PENALTY,
    REPETITION_PENALTY,
)
from tests.harness.client.errors import ServerError
from tests.harness.environment.settings import DEFAULT_GENDER, DEFAULT_SERVER_URL, DEFAULT_PERSONALITY

if TYPE_CHECKING:
    from argparse import Namespace, ArgumentParser
    from collections.abc import Coroutine


def add_connection_arguments(
    parser: ArgumentParser,
    *,
    server_help: str | None = None,
    is_api_key_included: bool = True,
) -> None:
    """Register standard connection flags for test utilities.

    - ``--server`` defaults to the ``SERVER_URL`` environment value or ``DEFAULT_SERVER_URL``.
    - ``--api-key`` defaults to the ``API_KEY`` environment value when included.
    - ``--timeout`` bounds one complete transaction.
    - ``--sanitize`` opts into server output sanitization.
    """
    default_server = os.getenv("SERVER_URL", DEFAULT_SERVER_URL)
    parser.add_argument(
        "--server",
        default=default_server,
        help=server_help or f"WebSocket server URL (default environment SERVER_URL or {DEFAULT_SERVER_URL})",
    )
    if is_api_key_included:
        parser.add_argument(
            "--api-key",
            default=os.getenv("API_KEY"),
            help="API key for authentication (default environment API_KEY)",
        )
    parser.add_argument(
        "--timeout",
        type=float,
        default=TRANSACTION_TIMEOUT_SECONDS,
        help=f"Maximum seconds for one complete transaction (default: {TRANSACTION_TIMEOUT_SECONDS:g})",
    )
    parser.add_argument(
        "--sanitize",
        action="store_true",
        help="Enable server output sanitization",
    )


def add_sampling_arguments(parser: ArgumentParser) -> None:
    """Register standard sampling override options shared across test clients."""
    parser.add_argument(
        "--temperature",
        type=float,
        help=f"Sampling temperature override (default server value: {TEMPERATURE})",
    )
    parser.add_argument(
        "--top-p",
        type=float,
        dest="top_p",
        help=f"Nucleus sampling probability (default server value: {TOP_P})",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        dest="top_k",
        help=f"Top-k sampling cap (default server value: {TOP_K})",
    )
    parser.add_argument(
        "--repetition-penalty",
        type=float,
        dest="repetition_penalty",
        help=f"Repetition penalty (default server value: {REPETITION_PENALTY})",
    )
    parser.add_argument(
        "--presence-penalty",
        type=float,
        dest="presence_penalty",
        help=f"Presence penalty (default server value: {PRESENCE_PENALTY})",
    )
    parser.add_argument(
        "--frequency-penalty",
        type=float,
        dest="frequency_penalty",
        help=f"Frequency penalty (default server value: {FREQUENCY_PENALTY})",
    )


def build_sampling_payload(arguments: Mapping[str, Any] | Namespace) -> dict[str, float | int | bool]:
    """Extract CLI sampling overrides into the payload format expected by the server."""
    if not isinstance(arguments, Mapping):
        arguments = vars(arguments)
    payload: dict[str, float | int | bool] = {}
    for field in ("temperature", "top_p", "top_k", "repetition_penalty", "presence_penalty", "frequency_penalty"):
        value = arguments.get(field)
        if value is not None:
            payload[field] = value
    if arguments.get("sanitize"):
        payload["sanitize_output"] = True
    return payload


def build_client_parser(description: str) -> ArgumentParser:
    """Create a parser that already holds the connection and sampling flags, with abbreviations off."""
    parser = argparse.ArgumentParser(description=description, allow_abbrev=False)
    add_connection_arguments(
        parser,
        server_help=f"WebSocket URL (default environment SERVER_URL or {DEFAULT_SERVER_URL})",
    )
    add_sampling_arguments(parser)
    return parser


def add_profile_arguments(parser: ArgumentParser) -> None:
    """Register gender and personality flags that default to the GENDER and PERSONALITY environment values."""
    parser.add_argument(
        "--gender",
        dest="gender",
        choices=["female", "male"],
        default=os.getenv("GENDER", DEFAULT_GENDER),
        help="gender",
    )
    parser.add_argument(
        "--personality",
        dest="personality",
        default=os.getenv("PERSONALITY", DEFAULT_PERSONALITY),
        help="personality (e.g., flirty, savage, warm)",
    )


def parse_client_arguments(parser: ArgumentParser) -> Namespace:
    """Parse the command line and attach the sampling overrides a client sends to the server."""
    arguments = parser.parse_args()
    arguments.sampling = build_sampling_payload(arguments)
    return arguments


def run_client(session: Coroutine[Any, Any, object]) -> None:
    """Run a client session to its end; a server error exits with status 1 and Ctrl-C exits quietly."""
    try:
        asyncio.run(session)
    except ServerError:
        sys.exit(1)
    except KeyboardInterrupt:
        pass


__all__ = [
    "add_connection_arguments",
    "add_profile_arguments",
    "add_sampling_arguments",
    "build_client_parser",
    "build_sampling_payload",
    "parse_client_arguments",
    "run_client",
]
