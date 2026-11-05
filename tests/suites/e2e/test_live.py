"""Interactive live WebSocket test client."""

from __future__ import annotations

from typing import TYPE_CHECKING
import asyncio
import logging

from tests.harness.client.cli import build_client_parser, parse_client_arguments
from tests.harness.logic.live.runner import LiveRunRequest, run_live_session
from tests.harness.environment.settings import DEFAULT_GENDER, DEFAULT_PERSONALITY

if TYPE_CHECKING:
    import argparse


def _parse_arguments() -> argparse.Namespace:
    parser = build_client_parser("Interactive live WebSocket test")
    parser.add_argument(
        "message",
        nargs="*",
        help="optional opener message (default: Hey!)",
    )
    parser.add_argument(
        "--gender",
        choices=["female", "male"],
        default=DEFAULT_GENDER,
        help=f"Prompt gender (default: {DEFAULT_GENDER})",
    )
    parser.add_argument(
        "--personality",
        default=DEFAULT_PERSONALITY,
        help=f"Prompt personality (default: {DEFAULT_PERSONALITY})",
    )
    return parse_client_arguments(parser)


def main() -> None:
    """Run the interactive live E2E client."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    arguments = _parse_arguments()

    asyncio.run(
        run_live_session(
            LiveRunRequest(
                server_url=arguments.server,
                api_key=arguments.api_key,
                gender=arguments.gender,
                personality=arguments.personality,
                timeout_seconds=arguments.timeout,
                sampling=arguments.sampling or None,
                message=arguments.message,
            ),
        ),
    )


if __name__ == "__main__":
    main()
