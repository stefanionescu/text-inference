"""Turn prompt fitting and streaming helpers."""

from __future__ import annotations

from .budget import fit_prompt_to_budget
from src.websocket.errors import send_error
from .runner import GenerationRequest, run_generation
from config.runtime.websocket import TEXT_LENGTH_ERROR_CODE
from src.websocket.transport import StreamResponseRequest, stream_response
from src.state.execution import PromptBudgetRequest, PromptFitResult, TurnContext, TurnRequest


async def fit_turn_prompt(context: TurnContext, request: TurnRequest) -> PromptFitResult | None:
    """Resolve the exact prompt budget or send a validation error."""
    try:
        return fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix=request.static_prefix,
                runtime_text=request.runtime_text,
                history_messages=request.history_messages,
                user_utterance=request.user_utterance,
                maximum_prompt_tokens=context.session_settings.maximum_context_length,
                maximum_user_tokens=context.session_settings.maximum_user_utterance_tokens,
            ),
            context.tokenizer,
        )
    except ValueError as exception:
        await send_error(context.websocket, code=TEXT_LENGTH_ERROR_CODE, message=str(exception))
        return None


async def run_fitted_turn(
    context: TurnContext,
    request: TurnRequest,
    prompt_fit: PromptFitResult,
) -> None:
    """Stream one already-fitted turn and commit the result."""
    stream = run_generation(
        GenerationRequest(
            state=context.state,
            prompt=prompt_fit.prompt,
            engine=context.engine,
            tokenizer=context.tokenizer,
            request_id=request.request_id,
            sampling_overrides=request.sampling_overrides,
            prompt_token_count=prompt_fit.prompt_tokens,
            session_settings=context.session_settings,
            timeout_settings=context.timeout_settings,
            sampling_settings=context.sampling_settings,
        ),
    )
    await stream_response(
        StreamResponseRequest(
            websocket=context.websocket,
            stream=stream,
            connection_state=context.state,
            user_utterance=prompt_fit.user_utterance,
            history_user_utterance=prompt_fit.user_utterance,
            session_runtime=context.session_runtime,
        ),
    )


__all__ = [
    "TurnContext",
    "TurnRequest",
    "fit_turn_prompt",
    "run_fitted_turn",
]
