"""Execution-related dataclasses."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from collections.abc import Awaitable, Callable

if TYPE_CHECKING:
    from fastapi import WebSocket
    from src.engines.protocol import Engine
    from src.tokens.tokenizer import ThreadSafeTokenizer
    from src.state.session import HistoryMessage, SessionState
    from src.state.settings import SamplingSettings, SessionSettings, TimeoutSettings

CancelCheck = Callable[[], bool | Awaitable[bool]] | None
CompletionCounter = Callable[[str], int]


@dataclass(slots=True)
class StreamConfig:
    """Configuration for streaming."""

    session_id: str
    request_id: str
    prompt: str
    sampling_parameters: Any
    engine: Engine
    timeout_seconds: float
    count_completion_tokens: CompletionCounter
    flush_milliseconds: float = 0.0
    cancellation_check: CancelCheck = None


@dataclass(frozen=True, slots=True)
class PromptFitResult:
    """Exact prompt-fit result used before engine calls."""

    history_messages: list[HistoryMessage]
    user_utterance: str
    prompt: str
    prompt_tokens: int


@dataclass(frozen=True, slots=True)
class PromptBudgetRequest:
    """Inputs required to fit a prompt into the context budget."""

    static_prefix: str
    runtime_text: str
    history_messages: list[HistoryMessage]
    user_utterance: str
    maximum_prompt_tokens: int
    maximum_user_tokens: int | None = None


@dataclass(frozen=True, slots=True)
class TurnContext:
    """Execution context for one fitted turn."""

    websocket: WebSocket
    state: SessionState
    session_runtime: Any
    engine: Engine
    tokenizer: ThreadSafeTokenizer
    session_settings: SessionSettings
    timeout_settings: TimeoutSettings
    sampling_settings: SamplingSettings


@dataclass(frozen=True, slots=True)
class TurnRequest:
    """Validated request inputs for one turn."""

    request_id: str
    static_prefix: str
    runtime_text: str
    history_messages: list[HistoryMessage]
    user_utterance: str
    sampling_overrides: dict[str, float | int] | None


__all__ = [
    "CancelCheck",
    "CompletionCounter",
    "PromptBudgetRequest",
    "PromptFitResult",
    "StreamConfig",
    "TurnContext",
    "TurnRequest",
]
