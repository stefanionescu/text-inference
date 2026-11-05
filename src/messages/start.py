"""Start-message bootstrap for initializing a session turn."""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Literal, cast
import logging

from src.session.state import HistoryMessage
from src.session.config import update_session_config
from src.telemetry.sentry import capture_error
from src.websocket.errors import send_error
from src.websocket.transport import safe_send_flat
from config.runtime.websocket import (
    WEBSOCKET_STATUS_OK,
    TEXT_LENGTH_ERROR_CODE,
    WEBSOCKET_ERROR_INVALID_PAYLOAD,
    WEBSOCKET_ERROR_INVALID_SETTINGS,
)
from src.telemetry.instruments import get_metrics

from .sampling import extract_sampling_overrides
from .validators import (
    PromptLimit,
    ValidationError,
    require_prompt,
    sanitize_prompt_limit,
    validate_required_gender,
    validate_required_personality,
)

if TYPE_CHECKING:
    from collections.abc import Callable

    from fastapi import WebSocket

    from src.session.state import SessionState
    from src.session.runtime import SessionRuntime

logger = logging.getLogger(__name__)


async def _close_validation_error(
    websocket: WebSocket,
    error: ValidationError,
) -> None:
    """Send a validation error and close the WebSocket.

    Args:
        websocket: Client socket that receives the error and then closes.
        error: Validation failure that selects the protocol error code and text.

    """
    settings_errors = {
        "missing_prompt",
        "invalid_prompt",
        "prompt_too_long",
    }
    error_code = (
        WEBSOCKET_ERROR_INVALID_SETTINGS if error.error_code in settings_errors else WEBSOCKET_ERROR_INVALID_PAYLOAD
    )
    await send_error(websocket, code=error_code, message=error.message)
    await websocket.close(code=1008)
    logger.info("turn_validation: error=%s; connection closed", error.error_code)


async def _send_turn_error(
    websocket: WebSocket,
    *,
    code: str,
    message: str,
    is_close_requested: bool = False,
) -> None:
    """Send a start-turn error and optionally close the socket.

    Args:
        websocket: Client socket that sent the start frame.
        code: Protocol error code; `bootstrap_start_turn` passes `TEXT_LENGTH_ERROR_CODE`.
        message: Error text from the failed history fit.
        is_close_requested: Whether the socket also closes after the error.

    """
    await send_error(websocket, code=code, message=message)
    if is_close_requested:
        await websocket.close(code=1008)


def _extract_prompt(
    message: dict[str, Any],
    *,
    count_tokens: Callable[[str], int],
    maximum_prompt_tokens: int,
) -> str:
    """Extract and sanitize the required start prompt.

    Args:
        message: Decoded start frame.
        count_tokens: Function that counts the tokens of the sanitized prompt.
        maximum_prompt_tokens: Largest allowed prompt size in tokens.

    Returns:
        The sanitized prompt.

    """
    raw_prompt = message.get("prompt")
    required_prompt = require_prompt(
        raw_prompt,
        error_code="missing_prompt",
        message="prompt is required",
    )
    return sanitize_prompt_limit(
        required_prompt,
        PromptLimit(
            field_label="prompt",
            invalid_error_code="invalid_prompt",
            too_long_error_code="prompt_too_long",
            maximum_tokens=maximum_prompt_tokens,
            count_tokens=count_tokens,
        ),
    )


def _start_inputs(
    message: dict[str, Any],
    *,
    count_tokens: Callable[[str], int],
    session_runtime: SessionRuntime,
) -> tuple[str, str, str, dict[str, float | int | bool]]:
    """Resolve profile fields, prompt, and sampling overrides for start.

    Args:
        message: Decoded start frame.
        count_tokens: Function that counts prompt tokens.
        session_runtime: Runtime that supplies the token limit and sampling bounds.

    Returns:
        Gender, personality, sanitized prompt, and sampling overrides.

    """
    gender = validate_required_gender(message.get("gender"))
    personality = validate_required_personality(message.get("personality"))
    prompt = _extract_prompt(
        message,
        count_tokens=count_tokens,
        maximum_prompt_tokens=session_runtime.session_settings.maximum_prompt_tokens,
    )
    sampling_overrides = extract_sampling_overrides(
        message,
        sampling_settings=session_runtime.sampling_settings,
    )
    return gender, personality, prompt, sampling_overrides


async def _start_inputs_checked(
    websocket: WebSocket,
    message: dict[str, Any],
    *,
    session_runtime: SessionRuntime,
) -> tuple[str, str, str, dict[str, float | int | bool]] | None:
    """Resolve start inputs or reject the WebSocket payload.

    Args:
        websocket: Client socket that closes when validation fails.
        message: Decoded start frame.
        session_runtime: Runtime that supplies the tokenizer and limits.

    Returns:
        Gender, personality, sanitized prompt, and sampling overrides, or None after a rejected payload.

    """
    try:
        tokenizer = session_runtime.tokenizer
        return _start_inputs(
            message,
            count_tokens=tokenizer.count,
            session_runtime=session_runtime,
        )
    except ValidationError as error:
        capture_error(error)
        get_metrics().phase_errors_total.add(1, {"phase": "validate", "error.type": "invalid_start"})
        await _close_validation_error(websocket, error)
        return None


def history_messages(
    session_runtime: SessionRuntime,
    state: SessionState,
    message: dict[str, Any],
) -> list[HistoryMessage]:
    """Import schema-validated start history through the history controller.

    Args:
        session_runtime: Runtime whose history controller stores and returns the messages.
        state: Session that receives the imported history.
        message: Decoded start frame with the schema-validated `history` list.

    Returns:
        The session history after any import.

    """
    if state.history_messages or not isinstance(message.get("history"), list):
        return session_runtime.history.get_messages(state)
    imported = [
        HistoryMessage(role=cast('Literal["user", "assistant"]', item["role"]), content=item["content"])
        for item in message["history"]
    ]
    session_runtime.history.set_mode_histories(state, history_messages=imported)
    return session_runtime.history.get_messages(state)


async def bootstrap_start_turn(
    websocket: WebSocket,
    message: dict[str, Any],
    state: SessionState,
    *,
    session_runtime: SessionRuntime,
) -> bool:
    """Initialize a fresh session from a start payload.

    Args:
        websocket: Client socket that receives the `done` frame or the error.
        message: Decoded start frame.
        state: Session state to initialize.
        session_runtime: Runtime that initializes the session and fits its history.

    Returns:
        True after the session starts; False after a validation error or an oversized history.

    """
    started_at = time.perf_counter()
    try:
        session_runtime.initialize_session(state)
        logger.info(
            "WS recv: start len(history)=%s",
            len(message.get("history", [])),
        )

        resolved = await _start_inputs_checked(
            websocket,
            message,
            session_runtime=session_runtime,
        )
        if resolved is None:
            return False
        gender, personality, prompt, sampling_overrides = resolved

        update_session_config(
            state,
            gender=gender,
            personality=personality,
            prompt=prompt,
            sampling=sampling_overrides or {},
        )
        history_messages(session_runtime, state, message)
        try:
            session_runtime.fit_start_history(
                state,
                static_prefix=prompt,
                runtime_text="",
            )
        except ValueError as exception:
            get_metrics().phase_errors_total.add(1, {"phase": "validate", "error.type": "seed_history_too_long"})
            await _send_turn_error(
                websocket,
                code=TEXT_LENGTH_ERROR_CODE,
                message=str(exception),
                is_close_requested=True,
            )
            return False
        await safe_send_flat(websocket, "done", status=WEBSOCKET_STATUS_OK)
        return True
    finally:
        get_metrics().phase_latency.record(max(0.0, time.perf_counter() - started_at), {"phase": "validate"})


__all__ = ["bootstrap_start_turn", "history_messages"]
