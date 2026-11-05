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
    `mise run test:e2e:conversation -- --server ws://127.0.0.1:8000/ws`
"""

from __future__ import annotations

from typing import TYPE_CHECKING
import logging

from tests.harness.client.cli import run_client, build_client_parser, parse_client_arguments
from tests.harness.logic.conversation import ConversationRunRequest, run_conversation
from tests.harness.environment.settings import DEFAULT_GENDER, DEFAULT_PERSONALITY
from tests.harness.messages.conversation import CONVERSATION_HISTORY_MESSAGES

if TYPE_CHECKING:
    import argparse


def _parse_arguments() -> argparse.Namespace:
    parser = build_client_parser("Conversation history regression test")
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
    return parse_client_arguments(parser)


def main() -> None:
    """Run the conversation E2E client."""
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    arguments = _parse_arguments()
    gender = arguments.gender or DEFAULT_GENDER
    personality = arguments.personality or DEFAULT_PERSONALITY
    request = ConversationRunRequest(
        server_url=arguments.server,
        api_key=arguments.api_key,
        prompts=CONVERSATION_HISTORY_MESSAGES,
        gender=gender,
        personality=personality,
        timeout_seconds=arguments.timeout,
        sampling=arguments.sampling or None,
    )
    run_client(run_conversation(request))


if __name__ == "__main__":
    main()
