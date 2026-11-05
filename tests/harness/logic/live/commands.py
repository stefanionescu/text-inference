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
    """Display the supported command list.

    Args:
        argument: Text after `/help`, which this command ignores.
        client: Live client that supplies the profile arguments for `print_help`.
        registry: Prompt registry, which this command ignores.

    Returns:
        Always False, so the input loop keeps running.

    """
    del argument, registry
    profile = client.session.profile
    print_help(profile.gender, profile.personality, is_verbose=True)
    return False


async def _handle_history_command(
    argument: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """Print accumulated conversation history.

    Args:
        argument: Text after `/history`, which this command ignores.
        client: Live client whose session history this command prints.
        registry: Unused prompt registry that the callback signature requires.

    Returns:
        Always False, so the session continues after the listing.

    """
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
    """List unique genders available in the prompt registry.

    Args:
        argument: Text after `/genders`, which this command ignores.
        client: Unused client that the callback signature requires.
        registry: Prompt registry whose genders this command lists.

    Returns:
        False, because listing genders leaves the loop running.

    """
    del argument, client
    logger.info("Available genders: %s", ", ".join(registry.available_genders()))
    return False


async def _handle_personalities_command(
    argument: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """List unique personalities available in the prompt registry.

    Args:
        argument: Text after `/personalities`, which this command ignores.
        client: Unused live client; the callback signature includes it.
        registry: Prompt registry whose personalities this command lists.

    Returns:
        False, because listing personalities leaves the loop running.

    """
    del argument, client
    logger.info("Available personalities: %s", ", ".join(registry.available_personalities()))
    return False


async def _handle_stats_command(
    argument: str,
    client: LiveClient,
    registry: PromptProfileRegistry,
) -> bool:
    """Toggle response metrics when invoked without arguments.

    Args:
        argument: Text after `/stats`; any text prints the usage line instead of toggling.
        client: Live client whose metric logging flag this command flips.
        registry: Prompt registry that `/stats` has no use for.

    Returns:
        False in both cases, so the input loop continues.

    """
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
    """Stop and close the live session.

    Args:
        argument: Text after `/stop`, which this command ignores.
        client: Live client that this command closes.
        registry: Prompt registry that `/stop` has no use for.

    Returns:
        Always True, so the input loop exits.

    """
    del argument, registry
    logger.info("Stopping live session...")
    await client.close()
    logger.info("Stopped live session.")
    return True


def print_help(gender: str, personality: str, *, is_verbose: bool = False) -> None:
    """Print the live profile banner or detailed command list.

    Args:
        gender: Gender shown in the banner.
        personality: Personality shown in the banner.
        is_verbose: Whether to print the command list instead of the banner.

    """
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
    """Dispatch one exact slash command without aliases.

    Args:
        command_line: Input line without its leading slash.
        client: Live client passed to the command callback.
        registry: Prompt registry passed to the command callback.

    Returns:
        The callback result, where True ends the input loop; an unknown command returns False.

    """
    command, *remaining_arguments = command_line.split(maxsplit=1)
    argument = remaining_arguments[0].strip() if remaining_arguments else ""
    command_callback = COMMAND_CALLBACKS.get(command.lower())
    if command_callback is None:
        logger.warning("Unknown command '/%s'. Type /help for options.", command)
        return False
    return await command_callback(argument, client, registry)


__all__ = ["dispatch_command", "print_help"]
