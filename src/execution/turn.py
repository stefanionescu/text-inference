"""Fit and stream a validated turn, retaining the visible response in history."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from dataclasses import dataclass
from src.websocket.errors import send_error
from src.telemetry.instruments import get_metrics
from src.websocket.transport import safe_send_flat
from .runner import GenerationRequest, run_generation
from .budget import PromptBudgetRequest, fit_prompt_to_budget
from config.runtime.websocket import WEBSOCKET_STATUS_OK, TEXT_LENGTH_ERROR_CODE

if TYPE_CHECKING:
    from fastapi import WebSocket
    from collections.abc import AsyncIterator
    from src.session.runtime import SessionRuntime
    from src.runtime.dependencies import RuntimeDependencies
    from src.session.state import HistoryMessage, SessionState


logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TurnRequest:
    """Validated plan for executing one start/message turn."""

    state: SessionState
    request_id: str
    static_prefix: str
    runtime_text: str
    history_messages: list[HistoryMessage]
    user_utterance: str
    sampling_overrides: dict[str, float | int | bool] | None = None


async def run_turn_execution(
    websocket: WebSocket,
    request: TurnRequest,
    runtime_dependencies: RuntimeDependencies,
) -> None:
    """Fit the prompt, stream generation, and commit the visible response."""
    settings = runtime_dependencies.settings
    try:
        prompt_fit = fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix=request.static_prefix,
                runtime_text=request.runtime_text,
                history_messages=request.history_messages,
                user_utterance=request.user_utterance,
                maximum_prompt_tokens=settings.session.maximum_context_length,
                maximum_user_tokens=settings.session.maximum_user_utterance_tokens,
            ),
            runtime_dependencies.tokenizer,
        )
    except ValueError as exception:
        await send_error(websocket, code=TEXT_LENGTH_ERROR_CODE, message=str(exception))
        return
    stream = run_generation(
        GenerationRequest(
            state=request.state,
            prompt=prompt_fit.prompt,
            engine=runtime_dependencies.engine,
            tokenizer=runtime_dependencies.tokenizer,
            request_id=request.request_id,
            sampling_overrides=request.sampling_overrides,
            prompt_token_count=prompt_fit.prompt_tokens,
            session_settings=settings.session,
            timeout_settings=settings.timeouts,
            sampling_settings=settings.sampling,
        ),
    )
    await stream_response(
        StreamResponseRequest(
            websocket=websocket,
            stream=stream,
            connection_state=request.state,
            user_utterance=prompt_fit.user_utterance,
            session_runtime=runtime_dependencies.session_runtime,
        ),
    )


@dataclass
class _StreamState:
    """Internal state for stream_response."""

    completion_text: str
    is_text_visible: bool
    is_interrupted: bool = False


@dataclass(frozen=True)
class StreamResponseRequest:
    """Inputs for streaming one model response to a websocket."""

    websocket: WebSocket
    stream: AsyncIterator[str]
    connection_state: SessionState
    user_utterance: str
    session_runtime: SessionRuntime
    initial_text: str = ""
    is_initial_text_sent: bool = True
    history_user_utterance: str | None = None


async def _send_initial_text(
    websocket: WebSocket,
    initial_text: str,
    state: _StreamState,
    *,
    is_already_sent: bool,
) -> None:
    """Send initial text when it was not already emitted."""
    if not initial_text or is_already_sent:
        return
    sent = await safe_send_flat(websocket, "token", text=initial_text)
    if sent:
        state.is_text_visible = True
    else:
        state.is_interrupted = True


async def _forward_stream_chunks(
    websocket: WebSocket,
    stream: AsyncIterator[str],
    state: _StreamState,
) -> None:
    """Forward generated stream chunks to the client."""
    async for chunk in stream:
        sent = await safe_send_flat(websocket, "token", text=chunk)
        if not sent:
            state.is_interrupted = True
            break
        state.completion_text += chunk
        state.is_text_visible = True


async def _send_completion_frames(websocket: WebSocket, state: _StreamState) -> None:
    """Send final and done frames for a completed stream."""
    sent_completion = await safe_send_flat(websocket, "final", status=WEBSOCKET_STATUS_OK, text=state.completion_text)
    if not sent_completion:
        state.is_interrupted = True
        return
    sent_done = await safe_send_flat(websocket, "done", status=WEBSOCKET_STATUS_OK)
    if not sent_done:
        state.is_interrupted = True


async def _handle_empty_output(websocket: WebSocket) -> None:
    """Report an empty model output to metrics and client."""
    logger.warning("empty model output")
    get_metrics().empty_model_output_total.add(1)
    await safe_send_flat(
        websocket,
        "error",
        status=500,
        code="internal_error",
        message="Model produced no output",
    )


async def stream_response(request: StreamResponseRequest) -> str:
    """Stream chunks, emit final/done messages, and record history."""
    history_user = (
        request.history_user_utterance if request.history_user_utterance is not None else request.user_utterance
    )
    state = _StreamState(
        completion_text=request.initial_text,
        is_text_visible=bool(request.initial_text) and request.is_initial_text_sent,
    )
    is_history_committed = False

    def _commit_history() -> None:
        """Commit streamed text to history at most once."""
        nonlocal is_history_committed
        is_history_commit_needed = bool(state.is_text_visible and state.completion_text)
        if is_history_committed or not is_history_commit_needed:
            return
        request.session_runtime.history.append_response(
            request.connection_state,
            history_user,
            state.completion_text,
        )
        is_history_committed = True

    try:
        await _send_initial_text(
            request.websocket,
            request.initial_text,
            state,
            is_already_sent=request.is_initial_text_sent,
        )
        if not state.is_interrupted:
            await _forward_stream_chunks(request.websocket, request.stream, state)
        if not state.is_interrupted:
            if not state.completion_text:
                await _handle_empty_output(request.websocket)
                return state.completion_text
            await _send_completion_frames(request.websocket, state)
    finally:
        _commit_history()
    return state.completion_text


__all__ = ["StreamResponseRequest", "TurnRequest", "run_turn_execution", "stream_response"]
