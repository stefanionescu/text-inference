"""Warmup client for the local FastAPI websocket.

Connects to the server, sends a start message with a random prompt, prints ACK,
collects the full response, and reports metrics.

Metrics reported:
- ttfb_ms: time from request send to first token
- total_ms: time from request send to done
- stream_ms: time from first token to done
- chunks: number of token messages received
- chars: size of final response (characters)
- first_three_words_ms: time from request send to first three words

Usage:
  mise run test:e2e:warmup
  mise run test:e2e:warmup -- "your custom message"
  mise run test:e2e:warmup -- --gender male --personality savage "hello there"

Env:
  SERVER_URL=ws://127.0.0.1:8000/ws
  API_KEY=your_api_key (required, no default)
  GENDER=female|male
  PERSONALITY=flirty

Note: API key authentication is required. The client sends it in the
``X-API-Key`` header.
"""

from __future__ import annotations

import sys
import asyncio
import logging
import argparse

from tests.harness.client.cli import add_sampling_arguments, build_sampling_payload, add_connection_arguments
from tests.harness.client.errors import ServerError
from tests.harness.logic.warmup.runner import run_warmup


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True, allow_abbrev=False)
    parser.add_argument("message", nargs="*", help="optional user message")

    add_connection_arguments(parser)
    add_sampling_arguments(parser)

    parser.add_argument(
        "--gender",
        dest="gender",
        choices=["female", "male"],
        help="gender",
    )
    parser.add_argument(
        "--personality",
        dest="personality",
        help="personality (e.g., flirty, savage, warm)",
    )
    parser.add_argument(
        "--double-ttfb",
        dest="is_double_ttfb_enabled",
        action="store_true",
        help="send two sequential start messages over one connection and log metrics per transaction",
    )
    arguments = parser.parse_args()
    arguments.sampling = build_sampling_payload(arguments)
    return arguments


def main() -> None:
    """Run the warmup E2E client."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    arguments = _parse_arguments()
    try:
        asyncio.run(run_warmup(arguments))
    except ServerError:
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
