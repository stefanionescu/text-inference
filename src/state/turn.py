"""Turn execution planning dataclasses."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from .session import HistoryMessage, SessionState


@dataclass(slots=True)
class TurnPlan:
    """Validated plan for executing one start/message turn."""

    state: SessionState
    request_id: str
    static_prefix: str
    runtime_text: str
    history_messages: list[HistoryMessage]
    user_utterance: str | None = None
    sampling_overrides: dict[str, float | int | bool] | None = None


__all__ = ["TurnPlan"]
