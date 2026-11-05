"""Interactive CLI entry point for the live WebSocket test client."""

from __future__ import annotations

import os
import signal
from typing import TYPE_CHECKING
import asyncio
import logging
import contextlib
from dataclasses import dataclass

from tests.harness.client.errors import TestClientError, IdleTimeoutError, InputClosedError, ConnectionClosedError
from tests.harness.reporting.terminal import cyan, yellow, write_line, write_text
from tests.harness.logic.live.commands import print_help, dispatch_command

if TYPE_CHECKING:
    from tests.state import StreamResult

    from .client import LiveClient
    from .profiles import PromptProfileRegistry


logger = logging.getLogger("live")


@dataclass(slots=True)
class InteractiveRunner:
    """Own the interactive CLI session lifecycle."""

    client: LiveClient
    registry: PromptProfileRegistry
    is_banner_shown: bool = True
    standard_input_task: asyncio.Task[str] | None = None
    close_task: asyncio.Task[None] | None = None
    _is_closing: bool = False

    async def run(self) -> None:
        """Execute the interactive loop until exit or disconnect."""
        loop = asyncio.get_running_loop()
        is_sigint_installed = self._install_sigint_hook(loop)
        loop_task: asyncio.Task[None] | None = None
        disconnect_task: asyncio.Task[None] | None = None
        try:
            loop_task, disconnect_task = self._start_background_tasks()
            await self._coordinate_tasks(loop_task, disconnect_task)
        finally:
            await self._finalize_task(loop_task)
            await self._finalize_task(disconnect_task)
            await self._finalize_task(self.close_task)
            if is_sigint_installed:
                loop.remove_signal_handler(signal.SIGINT)

    def _install_sigint_hook(self, loop: asyncio.AbstractEventLoop) -> bool:
        """Install a signal handler for graceful Ctrl+C handling."""
        is_installed = False
        try:
            loop.add_signal_handler(signal.SIGINT, self._handle_sigint)
        except (NotImplementedError, RuntimeError):
            logger.warning("Signal handlers unavailable; Ctrl+C may be noisy")
        else:
            is_installed = True
        return is_installed

    def _start_background_tasks(self) -> tuple[asyncio.Task[None], asyncio.Task[None]]:
        """Create background tasks for input loop and disconnect monitoring."""
        loop_task = asyncio.create_task(self._run_input_loop())
        disconnect_task = asyncio.create_task(self._watch_disconnect())
        return loop_task, disconnect_task

    async def _coordinate_tasks(
        self,
        loop_task: asyncio.Task[None],
        disconnect_task: asyncio.Task[None],
    ) -> None:
        """Wait for either input loop or disconnect, then clean up the other."""
        done, _ = await asyncio.wait(
            {loop_task, disconnect_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        is_disconnect_complete = disconnect_task in done
        if is_disconnect_complete:
            await self._cancel_task(
                loop_task,
                suppress=(asyncio.CancelledError, InputClosedError, ConnectionClosedError),
            )
        else:
            await self._cancel_task(disconnect_task)

    async def _cancel_task[TaskResult](
        self,
        task: asyncio.Task[TaskResult],
        *,
        suppress: tuple[type[BaseException], ...] = (asyncio.CancelledError,),
    ) -> None:
        """Cancel a task and suppress specified exceptions."""
        if task.done():
            return
        task.cancel()
        with contextlib.suppress(*suppress):
            await task

    async def _finalize_task[TaskResult](self, task: asyncio.Task[TaskResult] | None) -> None:
        """Ensure a task is cancelled and awaited during cleanup."""
        if not task:
            return
        is_task_complete = task.done()
        if not is_task_complete:
            await self._cancel_task(task)
        else:
            with contextlib.suppress(asyncio.CancelledError):
                await task

    async def _run_input_loop(self) -> None:
        """Run the input loop for commands and messages."""
        profile = self.client.session.profile
        if self.is_banner_shown:
            print_help(profile.gender, profile.personality)
        while True:
            line = await self._read_loop_line()
            if line is None:
                break
            if await self._dispatch_line(line):
                break

    async def _read_loop_line(self) -> str | None:
        """Read one input line, returning None when the loop should stop."""
        line: str | None = None
        try:
            line = await self._read_line()
        except InputClosedError as exception:
            if not self._is_closing:
                logger.info("%s", exception)
            else:
                logger.debug("stdin closed while shutting down: %s", exception)
            return None
        except TestClientError:
            logger.exception("send failed")
            raise
        return line

    async def _dispatch_line(self, line: str) -> bool:
        """Dispatch one input line and return whether the loop should exit."""
        is_exit_requested = False
        if not line:
            return is_exit_requested
        if line.startswith("/"):
            is_exit_requested = await dispatch_command(line[1:], self.client, self.registry)
        else:
            try:
                result = await self.client.send_user_message(line)
            except IdleTimeoutError:
                logger.warning("Connection closed due to inactivity; exiting.")
                is_exit_requested = True
            except ConnectionClosedError:
                logger.warning("Connection closed; exiting interactive mode.")
                is_exit_requested = True
            else:
                is_exit_requested = self._handle_stream_result(result)
        return is_exit_requested

    def _handle_stream_result(self, result: StreamResult) -> bool:
        """Handle a sent message result and return whether the loop should exit."""
        if result.is_successful:
            return False
        error_message = "" if result.error is None else result.error.format_for_user()
        self._print_error(error_message)
        if result.error is None or result.error.is_recoverable():
            return False
        logger.warning("Fatal error; exiting interactive mode.")
        return True

    async def _read_line(self) -> str:
        """Read a line from stdin asynchronously."""
        loop = asyncio.get_running_loop()
        if self.standard_input_task:
            self.standard_input_task.cancel()
        self.standard_input_task = loop.create_task(_read_standard_input(f"{cyan('USER')} "))
        try:
            line = await self.standard_input_task
        except asyncio.CancelledError as exception:
            message = "input cancelled"
            raise InputClosedError(message) from exception
        finally:
            self.standard_input_task = None
        return line.strip()

    def _handle_sigint(self) -> None:
        """Handle Ctrl+C by initiating graceful shutdown."""
        if self._is_closing:
            return
        self._is_closing = True
        logger.info("Ctrl+C received; closing session...")
        if self.standard_input_task:
            self.standard_input_task.cancel()
        self.close_task = asyncio.create_task(self.client.close())

    def _print_error(self, message: str) -> None:
        """Print an error message in a user-friendly format."""
        warning_label = yellow("WARN")
        prompt_label = cyan("USER")
        write_line(f"\n{warning_label}  {message}\n")
        write_text(f"{prompt_label} ", is_flush_requested=True)

    async def _watch_disconnect(self) -> None:
        """Monitor for server disconnect and trigger shutdown if needed."""
        try:
            await self.client.websocket.wait_closed()
        except asyncio.CancelledError:
            return
        if self._is_closing:
            return
        self._is_closing = True
        close_code = getattr(self.client.websocket, "close_code", None)
        close_reason = getattr(self.client.websocket, "close_reason", None)
        logger.warning(
            "Server closed the connection (code=%s reason=%s); exiting.",
            close_code,
            close_reason,
        )
        if self.standard_input_task:
            self.standard_input_task.cancel()
        os._exit(0)


async def _read_standard_input(prompt: str) -> str:
    """Async wrapper around input() that runs in an executor."""
    loop = asyncio.get_running_loop()
    prompt_text = prompt
    try:
        return await loop.run_in_executor(None, lambda: input(prompt_text))
    except EOFError as exception:
        message = "stdin closed"
        raise InputClosedError(message) from exception
    except KeyboardInterrupt as exception:
        message = "keyboard interrupt"
        raise InputClosedError(message) from exception


async def run_interactive_loop(
    client: LiveClient,
    registry: PromptProfileRegistry,
    *,
    is_banner_shown: bool = True,
) -> None:
    """Run the interactive command loop."""
    runner = InteractiveRunner(client, registry, is_banner_shown=is_banner_shown)
    await runner.run()


__all__ = ["run_interactive_loop"]
