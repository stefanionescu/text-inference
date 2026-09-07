"""Start-message bootstrap for initializing a session turn."""

from __future__ import annotations

import time
import logging
from .history import history_messages
from typing import TYPE_CHECKING, Any
from src.websocket.errors import send_error
from src.telemetry.sentry import capture_error
from .sampling import extract_sampling_overrides
from src.telemetry.instruments import get_metrics
from src.websocket.transport import safe_send_flat
from src.session.config import update_session_config
from .validators import (
    PromptLimit,
    require_prompt,
    ValidationError,
    sanitize_prompt_limit,
    validate_required_gender,
    validate_required_personality,
)
from config.runtime.websocket import (
    WEBSOCKET_STATUS_OK,
    TEXT_LENGTH_ERROR_CODE,
    WEBSOCKET_ERROR_INVALID_PAYLOAD,
    WEBSOCKET_ERROR_INVALID_SETTINGS,
)

if TYPE_CHECKING:
    from fastapi import WebSocket
    from collections.abc import Callable
    from src.state.session import SessionState
    from src.session.runtime import SessionRuntime

logger = logging.getLogger(__name__)


async def _close_validation_error(
    websocket: WebSocket,
    error: ValidationError,
) -> None:
    """Send a validation error and close the WebSocket."""
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
    """Send a start-turn error and optionally close the socket."""
    await send_error(websocket, code=code, message=message)
    if is_close_requested:
        await websocket.close(code=1008)


def _validate_profile_fields(message: dict[str, Any]) -> tuple[str, str]:
    """Validate required gender and personality fields from a start message."""
    return validate_required_gender(message.get("gender")), validate_required_personality(message.get("personality"))


def _extract_prompt(
    message: dict[str, Any],
    *,
    count_tokens: Callable[[str], int],
    maximum_prompt_tokens: int,
) -> str:
    """Extract and sanitize the required start prompt."""
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
    """Resolve profile fields, prompt, and sampling overrides for start."""
    gender, personality = _validate_profile_fields(message)
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
    """Resolve start inputs or reject the WebSocket payload."""
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


async def bootstrap_start_turn(
    websocket: WebSocket,
    message: dict[str, Any],
    state: SessionState,
    *,
    session_runtime: SessionRuntime,
) -> bool:
    """Initialize a fresh session from a start payload."""
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


__all__ = ["bootstrap_start_turn"]
