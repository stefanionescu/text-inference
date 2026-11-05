"""History recall test for warm history and prefix caching.

Connects to the WebSocket server with a pre-built conversation history, then
sends follow-up messages to test the assistant's recall of earlier exchanges.
Tracks TTFB for each response and prints summary statistics (p50, p90, p95).

Its flags default to the SERVER_URL, GENDER, and PERSONALITY environment
variables. API_KEY has no default and is required.

Usage:
  mise run test:e2e:history
  mise run test:e2e:history -- --gender male
  mise run test:e2e:history -- --temperature 0.8 --top-p 0.9
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.harness.client.cli import run_client, build_client_parser, add_profile_arguments, parse_client_arguments
from tests.harness.logic.history.runner import HistoryRunRequest, run_history_replay

if TYPE_CHECKING:
    import argparse


def _parse_arguments() -> argparse.Namespace:
    parser = build_client_parser("History recall test")
    add_profile_arguments(parser)
    return parse_client_arguments(parser)


def main() -> None:
    """Parse CLI arguments and run the finite history recall test."""
    arguments = _parse_arguments()
    request = HistoryRunRequest(
        server_url=arguments.server,
        api_key=arguments.api_key,
        gender=arguments.gender,
        personality=arguments.personality,
        timeout_seconds=arguments.timeout,
        sampling=arguments.sampling or None,
    )
    run_client(run_history_replay(request))


if __name__ == "__main__":
    main()
