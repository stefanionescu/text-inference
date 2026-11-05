"""Conversation history tester.

Opens a websocket session, reuses a single prompt profile, and replays a scripted
ten-turn conversation to verify that history retention and KV-cache behavior
remain stable under bounded-history constraints. Each exchange logs:
  - user + assistant text
  - time to first token (TTFB)
  - time to first three words
  - time to first complete sentence

Usage:
    mise run test:e2e:conversation
    mise run test:e2e:conversation -- --server ws://127.0.0.1:8000/ws
"""

from __future__ import annotations

import sys
import asyncio
import logging
import argparse

from tests.harness.client.cli import add_sampling_arguments, build_sampling_payload, add_connection_arguments
from tests.harness.client.errors import ServerError
from tests.harness.logic.conversation import ConversationRunRequest, run_conversation
from tests.harness.environment.settings import (
    DEFAULT_GENDER,
    DEFAULT_SERVER_URL,
    DEFAULT_PERSONALITY,
)
from tests.harness.messages.conversation import CONVERSATION_HISTORY_MESSAGES


def _parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Conversation history regression test", allow_abbrev=False)
    add_connection_arguments(
        parser,
        server_help=f"WebSocket URL (default environment SERVER_URL or {DEFAULT_SERVER_URL})",
    )
    add_sampling_arguments(parser)
    parser.add_argument(
        "--gender",
        dest="gender",
        help="Assistant gender override (defaults to environment value or DEFAULT_GENDER)",
    )
    parser.add_argument(
        "--personality",
        dest="personality",
        help="Assistant personality override (defaults to environment value or DEFAULT_PERSONALITY)",
    )
    arguments = parser.parse_args()
    arguments.sampling = build_sampling_payload(arguments)
    return arguments


def main() -> None:
    """Run the conversation E2E client."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    arguments = _parse_arguments()
    gender = arguments.gender or DEFAULT_GENDER
    personality = arguments.personality or DEFAULT_PERSONALITY
    try:
        asyncio.run(
            run_conversation(
                ConversationRunRequest(
                    server_url=arguments.server,
                    api_key=arguments.api_key,
                    prompts=CONVERSATION_HISTORY_MESSAGES,
                    gender=gender,
                    personality=personality,
                    timeout_seconds=arguments.timeout,
                    sampling=arguments.sampling or None,
                ),
            ),
        )
    except ServerError:
        sys.exit(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
