"""Execution entrypoint."""

from __future__ import annotations

from typing import TYPE_CHECKING
from src.state.execution import TurnContext, TurnRequest
from src.execution.turn import fit_turn_prompt, run_fitted_turn

if TYPE_CHECKING:
    from fastapi import WebSocket
    from src.state.session import SessionState
    from src.runtime.dependencies import RuntimeDependencies


def _build_turn_context(
    websocket: WebSocket,
    state: SessionState,
    runtime_dependencies: RuntimeDependencies,
) -> TurnContext:
    """Build a turn context from runtime dependencies."""
    return TurnContext(
        websocket=websocket,
        state=state,
        session_runtime=runtime_dependencies.session_runtime,
        engine=runtime_dependencies.engine,
        tokenizer=runtime_dependencies.tokenizer,
        session_settings=runtime_dependencies.settings.session,
        timeout_settings=runtime_dependencies.settings.timeouts,
        sampling_settings=runtime_dependencies.settings.sampling,
    )


async def run_turn_execution(
    websocket: WebSocket,
    state: SessionState,
    request: TurnRequest,
    *,
    runtime_dependencies: RuntimeDependencies,
) -> None:
    """Fit and run one generation turn."""
    context = _build_turn_context(websocket, state, runtime_dependencies)
    prompt_fit = await fit_turn_prompt(context, request)
    if prompt_fit is None:
        return
    await run_fitted_turn(context, request, prompt_fit)


__all__ = ["run_turn_execution"]
