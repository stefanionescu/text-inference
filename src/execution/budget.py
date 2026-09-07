"""Exact prompt budgeting helpers."""

from __future__ import annotations

from typing import TYPE_CHECKING
from dataclasses import dataclass
from src.execution.templates import build_prefixed_prompt
from src.state.execution import PromptBudgetRequest, PromptFitResult
from src.session.history.turns import copy_messages, flatten_turns, group_turns

if TYPE_CHECKING:
    from src.state.session import HistoryMessage
    from src.tokens.tokenizer import ThreadSafeTokenizer


@dataclass(frozen=True, slots=True)
class _PromptFitContext:
    """Immutable prompt fitting inputs shared across trim attempts."""

    static_prefix: str
    runtime_text: str
    history_turns: list[list[HistoryMessage]]
    tokenizer: ThreadSafeTokenizer
    maximum_prompt_tokens: int
    maximum_user_tokens: int | None


def _build_prompt(context: _PromptFitContext, user_utterance: str) -> tuple[str, int]:
    """Build a prompt candidate and count its tokens."""
    prompt = build_prefixed_prompt(
        context.static_prefix,
        context.runtime_text,
        flatten_turns(context.history_turns),
        user_utterance,
        context.tokenizer,
    )
    return prompt, len(context.tokenizer.encode_ids(prompt))


def _replace_history_turns(
    context: _PromptFitContext,
    history_turns: list[list[HistoryMessage]],
) -> _PromptFitContext:
    """Return a fit context with a different history window."""
    return _PromptFitContext(
        static_prefix=context.static_prefix,
        runtime_text=context.runtime_text,
        history_turns=history_turns,
        tokenizer=context.tokenizer,
        maximum_prompt_tokens=context.maximum_prompt_tokens,
        maximum_user_tokens=context.maximum_user_tokens,
    )


def _build_fit_context(request: PromptBudgetRequest, tokenizer: ThreadSafeTokenizer) -> _PromptFitContext:
    """Create prompt fitting context from a turn request."""
    return _PromptFitContext(
        static_prefix=request.static_prefix,
        runtime_text=request.runtime_text,
        history_turns=group_turns(copy_messages(request.history_messages)),
        tokenizer=tokenizer,
        maximum_prompt_tokens=request.maximum_prompt_tokens,
        maximum_user_tokens=request.maximum_user_tokens,
    )


def _count_user_tokens(user_utterance: str, tokenizer: ThreadSafeTokenizer) -> int:
    """Count tokens in a normalized user utterance."""
    return len(tokenizer.encode_ids((user_utterance or "").strip()))


def _limit_user_utterance(
    raw_user_utterance: str,
    tokenizer: ThreadSafeTokenizer,
    *,
    maximum_user_tokens: int | None,
) -> str:
    """Return the longest user text allowed by the user-token cap."""
    user_utterance = (raw_user_utterance or "").strip()
    if not user_utterance:
        return ""
    token_count = _count_user_tokens(user_utterance, tokenizer)
    capped_token_count = (
        token_count if maximum_user_tokens is None else min(token_count, max(1, int(maximum_user_tokens)))
    )
    return _trim_user_utterance(user_utterance, capped_token_count, tokenizer)


def _trim_user_utterance(
    raw_user_utterance: str,
    remaining_tokens: int,
    tokenizer: ThreadSafeTokenizer,
) -> str:
    """Trim raw user text to the requested token budget."""
    user_utterance = (raw_user_utterance or "").strip()
    if remaining_tokens <= 0 or not user_utterance:
        return ""
    return tokenizer.trim(
        user_utterance,
        maximum_tokens=remaining_tokens,
        retained_side="start",
    ).strip()


def _fit_user_utterance(context: _PromptFitContext, raw_user_utterance: str) -> tuple[str, str, int]:
    """Find the longest user text that fits the prompt context."""
    user_utterance = (raw_user_utterance or "").strip()
    if not user_utterance:
        prompt, prompt_tokens = _build_prompt(context, "")
        return "", prompt, prompt_tokens

    token_count = _count_user_tokens(user_utterance, context.tokenizer)
    capped_token_count = (
        token_count
        if context.maximum_user_tokens is None
        else min(token_count, max(1, int(context.maximum_user_tokens)))
    )
    lower_bound = 1
    upper_bound = capped_token_count
    best_fit: tuple[str, str, int] | None = None
    while lower_bound <= upper_bound:
        candidate_token_limit = (lower_bound + upper_bound) // 2
        trimmed_user_utterance = _trim_user_utterance(
            user_utterance,
            candidate_token_limit,
            context.tokenizer,
        )
        prompt, prompt_tokens = _build_prompt(context, trimmed_user_utterance)
        if prompt_tokens <= context.maximum_prompt_tokens:
            best_fit = (trimmed_user_utterance, prompt, prompt_tokens)
            lower_bound = candidate_token_limit + 1
        else:
            upper_bound = candidate_token_limit - 1

    if best_fit is not None:
        return best_fit

    message = "prompt exceeds exact context budget even after removing all history and trimming the user turn"
    raise ValueError(message)


def fit_prompt_to_budget(
    request: PromptBudgetRequest,
    tokenizer: ThreadSafeTokenizer,
) -> PromptFitResult:
    """Fit the exact templated prompt to budget with one raw-user fit path."""
    fit_context = _build_fit_context(request, tokenizer)
    effective_history = fit_context.history_turns
    limited_user_utterance = _limit_user_utterance(
        request.user_utterance,
        tokenizer,
        maximum_user_tokens=request.maximum_user_tokens,
    )
    prompt, prompt_tokens = _build_prompt(fit_context, limited_user_utterance)

    while effective_history and prompt_tokens > request.maximum_prompt_tokens:
        effective_history = effective_history[1:]
        fit_context = _replace_history_turns(fit_context, effective_history)
        prompt, prompt_tokens = _build_prompt(fit_context, limited_user_utterance)

    fitted_user_utterance, prompt, prompt_tokens = _fit_user_utterance(fit_context, request.user_utterance)

    if prompt_tokens > request.maximum_prompt_tokens:
        message = "prompt exceeds exact context budget before engine call"
        raise ValueError(message)

    return PromptFitResult(
        history_messages=flatten_turns(effective_history),
        user_utterance=fitted_user_utterance,
        prompt=prompt,
        prompt_tokens=prompt_tokens,
    )


__all__ = ["PromptBudgetRequest", "PromptFitResult", "fit_prompt_to_budget"]
