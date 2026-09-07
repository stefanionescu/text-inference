"""Message-turn planning for follow-up user utterances."""

from __future__ import annotations

import copy
import time
import uuid
from typing import TYPE_CHECKING
from .validators import ValidationError
from src.execution.turn import TurnRequest
from src.websocket.errors import send_error
from .sampling import extract_sampling_overrides
from src.telemetry.instruments import get_metrics
from src.session.config import update_session_config
from config.runtime.websocket import WEBSOCKET_ERROR_INVALID_MESSAGE, WEBSOCKET_ERROR_INVALID_PAYLOAD

if TYPE_CHECKING:
    from fastapi import WebSocket
    from collections.abc import Mapping
    from src.session.state import SessionState
    from src.session.runtime import SessionRuntime


async def _send_turn_error(
    websocket: WebSocket,
    *,
    code: str,
    message: str,
    is_close_requested: bool = False,
) -> None:
    """Send a turn-planning error and optionally close the socket."""
    await send_error(websocket, code=code, message=message)
    if is_close_requested:
        await websocket.close(code=1008)


def _build_message_turn_plan(
    state: SessionState,
    config: Mapping[str, object],
    incoming_user_utterance: str,
    *,
    sampling_overrides: dict[str, float | int | bool],
    session_runtime: SessionRuntime,
) -> TurnRequest:
    """Build a turn plan for a validated follow-up message."""
    prompt = config.get("prompt")
    return TurnRequest(
        state=state,
        request_id=f"message-{uuid.uuid4().hex}",
        static_prefix=prompt if isinstance(prompt, str) else "",
        runtime_text="",
        history_messages=session_runtime.history.get_messages(state),
        user_utterance=incoming_user_utterance,
        sampling_overrides=sampling_overrides or None,
    )


async def plan_message_turn(
    websocket: WebSocket,
    message: Mapping[str, object],
    state: SessionState,
    *,
    session_runtime: SessionRuntime,
) -> TurnRequest | None:
    """Build a validated turn plan from a follow-up message payload."""
    started_at = time.perf_counter()
    try:
        raw_user_utterance = message.get("user_utterance")
        incoming_user_utterance = raw_user_utterance.strip() if isinstance(raw_user_utterance, str) else ""
        if not incoming_user_utterance:
            get_metrics().phase_errors_total.add(1, {"phase": "validate", "error.type": "missing_user_utterance"})
            await _send_turn_error(
                websocket, code=WEBSOCKET_ERROR_INVALID_PAYLOAD, message="user_utterance is required"
            )
            return None

        config = copy.deepcopy(state.meta)
        if not config:
            get_metrics().phase_errors_total.add(1, {"phase": "validate", "error.type": "missing_session"})
            await _send_turn_error(
                websocket, code=WEBSOCKET_ERROR_INVALID_MESSAGE, message="no active session; send 'start' first"
            )
            return None

        try:
            sampling_overrides = extract_sampling_overrides(
                message,
                sampling_settings=session_runtime.sampling_settings,
            )
        except ValidationError as error:
            get_metrics().phase_errors_total.add(1, {"phase": "validate", "error.type": "invalid_sampling"})
            await _send_turn_error(
                websocket,
                code=WEBSOCKET_ERROR_INVALID_PAYLOAD,
                message=error.message,
                is_close_requested=True,
            )
            return None

        if sampling_overrides:
            update_session_config(
                state,
                sampling=sampling_overrides,
            )

        return _build_message_turn_plan(
            state,
            config,
            incoming_user_utterance,
            sampling_overrides=sampling_overrides,
            session_runtime=session_runtime,
        )
    finally:
        get_metrics().phase_latency.record(max(0.0, time.perf_counter() - started_at), {"phase": "validate"})


__all__ = ["plan_message_turn"]
