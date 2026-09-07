"""Unified turn handler for both ``start`` and ``message`` payloads."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from .message import plan_message_turn
from .start import bootstrap_start_turn
from typing import TYPE_CHECKING, Literal
from src.state.execution import TurnRequest
from src.execution.executor import run_turn_execution
from src.websocket.supervision import spawn_session_task

if TYPE_CHECKING:
    from fastapi import WebSocket
    from src.state.turn import TurnPlan
    from src.state.session import SessionState
    from src.session.runtime import SessionRuntime
    from src.runtime.dependencies import RuntimeDependencies

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TurnMessageRequest:
    """Inputs needed to handle one start or message command."""

    websocket: WebSocket
    message: dict[str, object]
    state: SessionState
    message_type: Literal["start", "message"]
    session_runtime: SessionRuntime
    runtime_dependencies: RuntimeDependencies


async def dispatch_execution(
    websocket: WebSocket,
    plan: TurnPlan,
    runtime_dependencies: RuntimeDependencies,
) -> None:
    """Dispatch a validated turn."""
    logger.info("turn_dispatch: streaming")
    await run_turn_execution(
        websocket,
        plan.state,
        TurnRequest(
            request_id=plan.request_id,
            static_prefix=plan.static_prefix,
            runtime_text=plan.runtime_text,
            history_messages=plan.history_messages,
            user_utterance=plan.user_utterance or "",
            sampling_overrides=plan.sampling_overrides,
        ),
        runtime_dependencies=runtime_dependencies,
    )


async def handle_turn_message(request: TurnMessageRequest) -> bool:
    """Plan and dispatch one session turn message."""
    if request.message_type == "start":
        return await bootstrap_start_turn(
            request.websocket,
            request.message,
            request.state,
            session_runtime=request.session_runtime,
        )

    plan = await plan_message_turn(
        request.websocket,
        request.message,
        request.state,
        session_runtime=request.session_runtime,
    )
    if plan is None:
        return False

    turn_dispatch = request.runtime_dependencies.turn_dispatch or dispatch_execution
    await spawn_session_task(
        request.websocket,
        request.state,
        request_id=plan.request_id,
        operation=turn_dispatch(request.websocket, plan, request.runtime_dependencies),
    )
    return True


__all__ = ["TurnMessageRequest", "dispatch_execution", "handle_turn_message"]
