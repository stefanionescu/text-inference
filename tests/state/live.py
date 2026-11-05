"""Live client dataclasses."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import field, dataclass

if TYPE_CHECKING:
    from tests.harness.client.errors import ServerError


@dataclass(frozen=True)
class PromptProfile:
    """Immutable protocol prompt profile."""

    gender: str
    personality: str
    prompt: str


@dataclass
class LiveSession:
    """Live test session state."""

    session_id: str
    profile: PromptProfile
    history: list[dict[str, str]] = field(default_factory=list)
    sampling: dict[str, float | int | bool] | None = None
    is_started: bool = False


@dataclass
class StreamResult:
    """Result of a streaming message exchange."""

    text: str
    is_successful: bool = True
    error: ServerError | None = None
    is_cancelled: bool = False


__all__ = [
    "LiveSession",
    "PromptProfile",
    "StreamResult",
]
