"""Session builders and WebSocket doubles for unit tests."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast
from dataclasses import field, replace, dataclass

from src.session.state import SessionState
from src.runtime.config import HistorySettings
from src.session.runtime import SessionRuntime
from tests.harness.environment.settings import DEFAULT_APPLICATION_SETTINGS

if TYPE_CHECKING:
    from fastapi import WebSocket

    from src.tokens.tokenizer import ThreadSafeTokenizer


@dataclass
class RecordingWebSocket:
    """WebSocket double that keeps every sent text frame and whether the socket closed.

    Attributes:
        sent: Frames that the test double sent.
        is_closed: Whether it is closed.
        close_code: Code of the close.

    """

    sent: list[str] = field(default_factory=list)
    is_closed: bool = False
    close_code: int | None = None

    async def send_text(self, text: str) -> None:
        """Keep the frame for later assertions.

        Args:
            text: Text to process.

        """
        self.sent.append(text)

    async def close(self, code: int = 1008) -> None:
        """Record the close and its code, which defaults to policy violation.

        Args:
            code: Error or close code.

        """
        self.is_closed = True
        self.close_code = code


def typed_websocket(double: object) -> WebSocket:
    """Hand a double to code that expects a WebSocket; the double defines only the methods that code calls.

    Args:
        double: Double.

    Returns:
        The web socket.

    """
    return cast("WebSocket", double)


def build_session_runtime(
    tokenizer: ThreadSafeTokenizer,
    *,
    trigger_tokens: int = 1000,
    target_tokens: int = 800,
) -> SessionRuntime:
    """Return a runtime whose history limits stay out of the way unless a test lowers them.

    Args:
        tokenizer: Tokenizer to use.
        trigger_tokens: Token count of the trigger.
        target_tokens: Token count of the target.

    Returns:
        A runtime whose history limits stay out of the way unless a test lowers them.

    """
    history_settings = HistorySettings(trigger_tokens=trigger_tokens, target_tokens=target_tokens)
    return SessionRuntime(
        tokenizer=tokenizer,
        settings=replace(DEFAULT_APPLICATION_SETTINGS, history=history_settings),
    )


def build_session_state(session_runtime: SessionRuntime) -> SessionState:
    """Return state the runtime has initialized, as a new connection starts with.

    Args:
        session_runtime: Session runtime.

    Returns:
        State the runtime has initialized, as a new connection starts with.

    """
    state = SessionState(meta={})
    session_runtime.initialize_session(state)
    return state


__all__ = ["RecordingWebSocket", "build_session_runtime", "build_session_state", "typed_websocket"]
