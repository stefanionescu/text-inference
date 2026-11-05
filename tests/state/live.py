"""Live client dataclasses."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import field, dataclass

if TYPE_CHECKING:
    from tests.harness.client.errors import ServerError


@dataclass(frozen=True)
class PromptProfile:
    """Immutable protocol prompt profile.

    Attributes:
        gender: Name of the gender profile.
        personality: Name of the personality profile.
        prompt: Prompt text.

    """

    gender: str
    personality: str
    prompt: str


@dataclass
class LiveSession:
    """Live test session state.

    Attributes:
        session_id: ID of the session.
        profile: Prompt profile to use.
        history: Conversation history to use.
        sampling: Sampling overrides of the request.
        is_started: Whether it is started.

    """

    session_id: str
    profile: PromptProfile
    history: list[dict[str, str]] = field(default_factory=list)
    sampling: dict[str, float | int | bool] | None = None
    is_started: bool = False


@dataclass
class StreamResult:
    """Result of a streaming message exchange.

    Attributes:
        text: Text to process.
        is_successful: Whether it is successful.
        error: Error text or error object to report.
        is_cancelled: Whether it is cancelled.

    """

    text: str
    is_successful: bool = True
    error: ServerError | None = None
    is_cancelled: bool = False


__all__ = [
    "LiveSession",
    "PromptProfile",
    "StreamResult",
]
