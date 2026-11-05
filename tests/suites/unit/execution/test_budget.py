"""Unit tests for exact prompt budgeting."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.execution.budget import PromptBudgetRequest, fit_prompt_to_budget
from tests.harness.messages.unit import MESSAGES, ASSISTANT_FIRST_MESSAGES
from tests.harness.environment.tokenizer import use_local_tokenizers, use_punctuation_aware_tokenizers

if TYPE_CHECKING:
    from src.session.state import HistoryMessage
    from src.execution.budget import PromptFitResult
    from src.tokens.tokenizer import ThreadSafeTokenizer

HISTORY_FIT_LIMIT = 70
ASSISTANT_GROUP_LIMIT = 60
TRIM_USER_LIMIT = 5
USER_CAP_FIT_LIMIT = 20
PUNCTUATION_FIT_LIMIT = 100
LONG_USER_TEXT = "hello can you help me plan a trip to lisbon next week"
OVERSIZED_PREFIX = "alpha bravo charlie delta"


def _fit_prompt(
    tokenizer: ThreadSafeTokenizer,
    user_utterance: str,
    maximum_prompt_tokens: int,
    *,
    history_messages: list[HistoryMessage] | None = None,
    static_prefix: str = "",
    maximum_user_tokens: int | None = None,
) -> PromptFitResult:
    """Fit a prompt with no runtime text and, unless a test passes them, no history or static prefix."""
    return fit_prompt_to_budget(
        PromptBudgetRequest(
            static_prefix=static_prefix,
            runtime_text="",
            history_messages=history_messages or [],
            user_utterance=user_utterance,
            maximum_prompt_tokens=maximum_prompt_tokens,
            maximum_user_tokens=maximum_user_tokens,
        ),
        tokenizer,
    )


def test_budget_keeps_history() -> None:
    """Test prompt fitting keeps the newest complete history groups."""
    with use_local_tokenizers() as tokenizer:
        fit = _fit_prompt(tokenizer, "hello", HISTORY_FIT_LIMIT, history_messages=MESSAGES)

        assert fit.history_messages == MESSAGES[-4:]
        assert fit.user_utterance == "hello"
        assert fit.prompt_tokens <= HISTORY_FIT_LIMIT


def test_budget_drops_group() -> None:
    """Test prompt fitting drops an incomplete leading history group."""
    with use_local_tokenizers() as tokenizer:
        fit = _fit_prompt(tokenizer, "hello", 40, history_messages=MESSAGES[:4])

        assert [(message.role, message.content) for message in fit.history_messages] == [
            ("user", "i need a quiet hotel near the river and my budget is moderate"),
            ("assistant", "a quiet riverside hotel in lisbon can work and i can suggest neighborhoods"),
        ]


def test_budget_keeps_assistant() -> None:
    """Test prompt fitting preserves a valid assistant-first history."""
    with use_local_tokenizers() as tokenizer:
        fit = _fit_prompt(
            tokenizer,
            "also remind me to pack a rain jacket and travel adapter",
            200,
            history_messages=ASSISTANT_FIRST_MESSAGES[:4],
        )

        assert fit.history_messages == ASSISTANT_FIRST_MESSAGES[:4]
        assert fit.prompt.startswith(
            "<|im_start|>assistant\n"
            "hello can you help me plan a trip to lisbon next week\n\n"
            "sure tell me your budget and hotel area preference",
        )
        if "<|im_start|>user\ni need a quiet hotel near the river and my budget is moderate" not in fit.prompt:
            pytest.fail("Assertion failed")


def test_budget_trims_groups() -> None:
    """Test prompt fitting trims assistant-first history by complete groups."""
    with use_local_tokenizers() as tokenizer:
        fit = _fit_prompt(tokenizer, "hello", ASSISTANT_GROUP_LIMIT, history_messages=ASSISTANT_FIRST_MESSAGES)

        assert fit.history_messages == ASSISTANT_FIRST_MESSAGES[-2:]
        assert fit.prompt_tokens <= ASSISTANT_GROUP_LIMIT


def test_budget_trims_user() -> None:
    """Test prompt fitting trims user text to the exact token budget."""
    with use_local_tokenizers() as tokenizer:
        fit = _fit_prompt(tokenizer, LONG_USER_TEXT, TRIM_USER_LIMIT)

        assert fit.history_messages == []
        assert fit.user_utterance == "hello can"
        assert fit.prompt_tokens <= TRIM_USER_LIMIT


def test_budget_rejects_static() -> None:
    """Test prompt fitting rejects a static prompt that exceeds the budget."""
    with use_local_tokenizers() as tokenizer, pytest.raises(ValueError, match="prompt exceeds exact context budget"):
        _fit_prompt(tokenizer, "", 1, static_prefix=OVERSIZED_PREFIX)


def test_budget_applies_cap() -> None:
    """Test prompt fitting applies the configured user token cap."""
    with use_local_tokenizers() as tokenizer:
        fit = _fit_prompt(tokenizer, LONG_USER_TEXT, USER_CAP_FIT_LIMIT, maximum_user_tokens=4)

        assert fit.user_utterance == "hello can you help"
        assert fit.prompt_tokens <= USER_CAP_FIT_LIMIT


def test_budget_rejects_user() -> None:
    """Test prompt fitting rejects text when no user token can fit."""
    with use_local_tokenizers() as tokenizer, pytest.raises(ValueError, match="prompt exceeds exact context budget"):
        _fit_prompt(tokenizer, "echo", 1, static_prefix=OVERSIZED_PREFIX)


def test_budget_keeps_punctuation() -> None:
    """Test user-token capping preserves tokenizer-aware punctuation."""
    with use_punctuation_aware_tokenizers() as tokenizer:
        fit = _fit_prompt(
            tokenizer,
            "remind me: passport, charger, adapters!",
            PUNCTUATION_FIT_LIMIT,
            maximum_user_tokens=4,
        )

        assert fit.history_messages == []
        assert fit.user_utterance == "remind me: passport"
        assert fit.prompt_tokens <= PUNCTUATION_FIT_LIMIT
