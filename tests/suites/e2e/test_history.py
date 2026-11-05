"""History recall test for warm history and prefix caching.

Connects to the WebSocket server with a pre-built conversation history, then
sends follow-up messages to test the assistant's recall of earlier exchanges.
Tracks TTFB for each response and prints summary statistics (p50, p90, p95).

Environment Variables:
- SERVER_URL: WebSocket URL (default: ws://127.0.0.1:8000/ws)
- API_KEY: API key for authentication (required, no default)
- GENDER: female|male (default: female)
- PERSONALITY: personality (default: flirty)

Usage:
  mise run test:e2e:history
  mise run test:e2e:history -- --gender male
  mise run test:e2e:history -- --temperature 0.8 --top-p 0.9
"""

from __future__ import annotations

import os
import sys
import asyncio
import argparse

from tests.harness.client.cli import add_sampling_arguments, build_sampling_payload, add_connection_arguments
from tests.harness.client.errors import ServerError
from tests.harness.environment.settings import DEFAULT_GENDER, DEFAULT_SERVER_URL, DEFAULT_PERSONALITY
from tests.harness.logic.history.runner import HistoryRunRequest, run_history_replay


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="History recall test", allow_abbrev=False)
    add_connection_arguments(
        parser,
        server_help=f"WebSocket URL (default environment SERVER_URL or {DEFAULT_SERVER_URL})",
    )
    add_sampling_arguments(parser)
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
    arguments = parser.parse_args()
    arguments.sampling = build_sampling_payload(arguments)
    return arguments


def _run_history_replay(arguments: argparse.Namespace) -> None:
    """Run the finite history recall test."""
    try:
        asyncio.run(
            run_history_replay(
                HistoryRunRequest(
                    server_url=arguments.server,
                    api_key=arguments.api_key,
                    gender=arguments.gender,
                    personality=arguments.personality,
                    timeout_seconds=arguments.timeout,
                    sampling=arguments.sampling or None,
                ),
            ),
        )
    except ServerError:
        sys.exit(1)
    except KeyboardInterrupt:
        pass


def main() -> None:
    """Parse CLI arguments and run history replay."""
    arguments = _parse_arguments()
    _run_history_replay(arguments)


if __name__ == "__main__":
    main()
