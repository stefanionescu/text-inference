"""Concurrent benchmark for the WebSocket /ws endpoint.

Runs N total sessions with up to M concurrent connections. For each request,
records:
- ttfb_ms: time to first token
- first_sentence_ms: time to first complete sentence
- first_3_words_ms: time to first three words

Prints p50/p95 for each metric across completed requests. No intermediate logs.

Environment Variables:
- SERVER_URL: WebSocket URL (default: ws://127.0.0.1:8000/ws)
- API_KEY: API key for authentication (required, no default)
- GENDER: female|male (default: female)
- PERSONALITY: personality (default: flirty)

Note: API key authentication is required. The client sends it in the
``X-API-Key`` header on every WebSocket connection.

If concurrency exceeds the server's MAX_CONCURRENT_CONNECTIONS limit, the
benchmark will surface the resulting "server_at_capacity" errors so you can
see how many sessions were rejected by the guardrail.
"""

from __future__ import annotations

import os
import sys
import asyncio
import argparse

from config.tests.defaults import (
    BENCHMARK_DEFAULT_REQUESTS,
    BENCHMARK_DEFAULT_CONCURRENCY,
)
from tests.harness.client.cli import add_sampling_arguments, build_sampling_payload, add_connection_arguments
from tests.harness.environment.settings import DEFAULT_GENDER, DEFAULT_SERVER_URL, DEFAULT_PERSONALITY
from tests.harness.logic.benchmark.runner import run_benchmark


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Benchmark Text Inference WS server", allow_abbrev=False)
    add_connection_arguments(
        parser,
        server_help=f"WebSocket URL (default environment SERVER_URL or {DEFAULT_SERVER_URL})",
    )
    add_sampling_arguments(parser)
    parser.add_argument("message", nargs="*", help="optional user message for all requests")
    _add_benchmark_arguments(parser)
    arguments = parser.parse_args()
    arguments.sampling = build_sampling_payload(arguments)
    return arguments


def _add_benchmark_arguments(parser: argparse.ArgumentParser) -> None:
    """Add benchmark-specific CLI arguments."""
    parser.add_argument(
        "--requests",
        "-r",
        type=int,
        default=BENCHMARK_DEFAULT_REQUESTS,
        help="total number of requests",
    )
    parser.add_argument(
        "--concurrency",
        "-c",
        type=int,
        default=BENCHMARK_DEFAULT_CONCURRENCY,
        help="max in-flight requests",
    )
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
    parser.add_argument(
        "--double-ttfb",
        dest="is_double_ttfb_enabled",
        action="store_true",
        help="send two sequential turns per connection and report metrics separately",
    )


def main() -> None:
    """Parse command-line arguments and run the benchmark."""
    arguments = _parse_arguments()
    is_successful = asyncio.run(run_benchmark(arguments))
    if not is_successful:
        sys.exit(1)


if __name__ == "__main__":
    main()
