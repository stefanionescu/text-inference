"""Interactive live WebSocket test client."""

from __future__ import annotations

import asyncio
import logging
import argparse
from tests.harness.logic.live.runner import LiveRunRequest, run_live_session
from tests.harness.environment.settings import DEFAULT_GENDER, DEFAULT_PERSONALITY, DEFAULT_SERVER_URL
from tests.harness.client.cli import add_connection_arguments, add_sampling_arguments, build_sampling_payload


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Interactive live WebSocket test", allow_abbrev=False)
    add_connection_arguments(
        parser,
        server_help=f"WebSocket URL (default environment SERVER_URL or {DEFAULT_SERVER_URL})",
    )
    add_sampling_arguments(parser)
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
    arguments = parser.parse_args()
    arguments.sampling = build_sampling_payload(arguments)
    return arguments


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
