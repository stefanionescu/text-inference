"""Slash commands for the interactive live client."""

from __future__ import annotations

from typing import TYPE_CHECKING
import logging
from collections.abc import Callable, Awaitable

from tests.harness.reporting.terminal import dim, bold, write_line

if TYPE_CHECKING:
    from .client import LiveClient
    from .profiles import PromptProfileRegistry

logger = logging.getLogger("live")


async def _handle_help_command(
    argument: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """Display the supported command list."""
    del argument, registry
    profile = client.session.profile
    print_help(profile.gender, profile.personality, is_verbose=True)
    return False


async def _handle_history_command(
    argument: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """Print accumulated conversation history."""
    del argument, registry
    if not client.session.history:
        logger.info("History is empty")
        return False
    write_line("\n--- conversation history ---")
    for message in client.session.history:
        role = message.get("role", "unknown").capitalize()
        content = message.get("content", "")
        write_line(f"{role}: {content}")
    write_line("--- end history ---")
    return False


async def _handle_genders_command(
    argument: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """List unique genders available in the prompt registry."""
    del argument, client
    logger.info("Available genders: %s", ", ".join(registry.available_genders()))
    return False


async def _handle_personalities_command(
    argument: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """List unique personalities available in the prompt registry."""
    del argument, client
    logger.info("Available personalities: %s", ", ".join(registry.available_personalities()))
    return False


async def _handle_stats_command(
    argument: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """Toggle response metrics when invoked without arguments."""
    del registry
    if argument:
        logger.warning("Usage: /stats")
        return False
    client.is_stats_logging_enabled = not client.is_stats_logging_enabled
    logger.info("Stats logging %s", "enabled" if client.is_stats_logging_enabled else "disabled")
    return False


async def _handle_stop_command(
    argument: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """Stop and close the live session."""
    del argument, registry
    logger.info("Stopping live session...")
    await client.close()
    logger.info("Stopped live session.")
    return True


def print_help(gender: str, personality: str, *, is_verbose: bool = False) -> None:
    """Print the live profile banner or detailed command list."""
    if is_verbose:
        write_line(
            f"\n{bold('Commands:')}\n"
            f"  {dim('/help')}           Show this command list\n"
            f"  {dim('/history')}        Print accumulated conversation history\n"
            f"  {dim('/genders')}        List available genders\n"
            f"  {dim('/personalities')}  List available personalities\n"
            f"  {dim('/stats')}          Toggle metrics logging\n"
            f"  {dim('/stop')}           Stop and close the session\n"
            "\nAny line without a leading '/' is sent to the assistant.\n",
        )
        return
    write_line(
        f"\n{bold('Interactive mode ready.')} Type /help for commands.\nCurrent profile: {gender}/{personality}\n",
    )


CommandCallback = Callable[[str, "LiveClient", "PromptProfileRegistry"], Awaitable[bool]]

COMMAND_CALLBACKS: dict[str, CommandCallback] = {
    "genders": _handle_genders_command,
    "help": _handle_help_command,
    "history": _handle_history_command,
    "personalities": _handle_personalities_command,
    "stats": _handle_stats_command,
    "stop": _handle_stop_command,
}


async def dispatch_command(
    command_line: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """Dispatch one exact slash command without aliases."""
    command, *remaining_arguments = command_line.split(maxsplit=1)
    argument = remaining_arguments[0].strip() if remaining_arguments else ""
    command_callback = COMMAND_CALLBACKS.get(command.lower())
    if command_callback is None:
        logger.warning("Unknown command '/%s'. Type /help for options.", command)
        return False
    return await command_callback(argument, client, registry)


__all__ = ["dispatch_command", "print_help"]
