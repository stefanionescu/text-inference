"""Unified turn handler for both ``start`` and ``message`` payloads."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal
import logging
from dataclasses import dataclass

from src.execution.turn import run_turn_execution
from src.session.requests import spawn_session_task
from src.websocket.supervision import supervise_turn

from .start import bootstrap_start_turn
from .message import plan_message_turn

if TYPE_CHECKING:
    from fastapi import WebSocket

    from src.session.state import SessionState
    from src.runtime.dependencies import RuntimeDependencies

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TurnMessageRequest:
    """Inputs needed to handle one start or message command.

    Attributes:
        websocket: WebSocket connection of the client.
        message: Message to send, check, or report.
        state: State of the session or test run.
        message_type: Type of the message.
        runtime_dependencies: Runtime dependencies.

    """

    websocket: WebSocket
    message: dict[str, object]
    state: SessionState
    message_type: Literal["start", "message"]
    runtime_dependencies: RuntimeDependencies


async def handle_turn_message(request: TurnMessageRequest) -> bool:
    """Plan and dispatch one session turn message.

    Args:
        request: Request to run.

    Returns:
        Whether the check passes.

    """
    if request.message_type == "start":
        return await bootstrap_start_turn(
            request.websocket,
            request.message,
            request.state,
            session_runtime=request.runtime_dependencies.session_runtime,
        )

    plan = await plan_message_turn(
        request.websocket,
        request.message,
        request.state,
        session_runtime=request.runtime_dependencies.session_runtime,
    )
    if plan is None:
        return False

    await spawn_session_task(
        request.state,
        request_id=plan.request_id,
        operation=lambda: supervise_turn(
            request.websocket,
            lambda: run_turn_execution(request.websocket, plan, request.runtime_dependencies),
            request_id=plan.request_id,
            state=request.state,
        ),
    )
    return True


__all__ = ["TurnMessageRequest", "handle_turn_message"]
