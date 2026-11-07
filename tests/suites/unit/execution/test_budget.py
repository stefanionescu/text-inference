"""Unit tests for exact prompt budgeting."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from src.execution.budget import PromptBudgetRequest, fit_prompt_to_budget
from tests.harness.messages.unit import MESSAGES, ASSISTANT_FIRST_MESSAGES
from tests.harness.environment.tokenizer import use_local_tokenizers, use_punctuation_aware_tokenizers

if TYPE_CHECKING:
    from src.session.state import HistoryMessage

HISTORY_FIT_LIMIT = 70
ASSISTANT_GROUP_LIMIT = 60
TRIM_USER_LIMIT = 5
USER_CAP_FIT_LIMIT = 20
PUNCTUATION_FIT_LIMIT = 100
LONG_USER_TEXT = "hello can you help me plan a trip to lisbon next week"
OVERSIZED_PREFIX = "alpha bravo charlie delta"


def _budget_request(
    user_utterance: str,
    maximum_prompt_tokens: int,
    *,
    history_messages: list[HistoryMessage] | None = None,
    static_prefix: str = "",
    maximum_user_tokens: int | None = None,
) -> PromptBudgetRequest:
    """Build a request with no runtime text and, unless a test passes them, no history or static prefix.

    Args:
        user_utterance: Text of the current user turn.
        maximum_prompt_tokens: Token budget of the whole prompt.
        history_messages: Earlier messages to fit, or None for a new session.
        static_prefix: System prompt text.
        maximum_user_tokens: Token cap of the user turn, or None for no cap.

    Returns:
        The request that `fit_prompt_to_budget` reads.

    """
    return PromptBudgetRequest(
        static_prefix=static_prefix,
        runtime_text="",
        history_messages=history_messages or [],
        user_utterance=user_utterance,
        maximum_prompt_tokens=maximum_prompt_tokens,
        maximum_user_tokens=maximum_user_tokens,
    )


def test_budget_keeps_history() -> None:
    """Test prompt fitting keeps the newest complete history groups."""
    with use_local_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(_budget_request("hello", HISTORY_FIT_LIMIT, history_messages=MESSAGES), tokenizer)

        assert fit.history_messages == MESSAGES[-4:]
        assert fit.user_utterance == "hello"
        assert fit.prompt_tokens <= HISTORY_FIT_LIMIT


def test_budget_drops_group() -> None:
    """Test prompt fitting drops an incomplete leading history group."""
    with use_local_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(_budget_request("hello", 40, history_messages=MESSAGES[:4]), tokenizer)

        assert [(message.role, message.content) for message in fit.history_messages] == [
            ("user", "i need a quiet hotel near the river and my budget is moderate"),
            ("assistant", "a quiet riverside hotel in lisbon can work and i can suggest neighborhoods"),
        ]


def test_budget_keeps_assistant() -> None:
    """Test prompt fitting preserves a valid assistant-first history."""
    with use_local_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(
            _budget_request(
                "also remind me to pack a rain jacket and travel adapter",
                200,
                history_messages=ASSISTANT_FIRST_MESSAGES[:4],
            ),
            tokenizer,
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
        fit = fit_prompt_to_budget(
            _budget_request("hello", ASSISTANT_GROUP_LIMIT, history_messages=ASSISTANT_FIRST_MESSAGES), tokenizer
        )

        assert fit.history_messages == ASSISTANT_FIRST_MESSAGES[-2:]
        assert fit.prompt_tokens <= ASSISTANT_GROUP_LIMIT


def test_budget_trims_user() -> None:
    """Test prompt fitting trims user text to the exact token budget."""
    with use_local_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(_budget_request(LONG_USER_TEXT, TRIM_USER_LIMIT), tokenizer)

        assert fit.history_messages == []
        assert fit.user_utterance == "hello can"
        assert fit.prompt_tokens <= TRIM_USER_LIMIT


def test_budget_rejects_static() -> None:
    """Test prompt fitting rejects a static prompt that exceeds the budget."""
    with use_local_tokenizers() as tokenizer, pytest.raises(ValueError, match="prompt exceeds exact context budget"):
        fit_prompt_to_budget(_budget_request("", 1, static_prefix=OVERSIZED_PREFIX), tokenizer)


def test_budget_applies_cap() -> None:
    """Test prompt fitting applies the configured user token cap."""
    with use_local_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(
            _budget_request(LONG_USER_TEXT, USER_CAP_FIT_LIMIT, maximum_user_tokens=4), tokenizer
        )

        assert fit.user_utterance == "hello can you help"
        assert fit.prompt_tokens <= USER_CAP_FIT_LIMIT


def test_budget_rejects_user() -> None:
    """Test prompt fitting rejects text when no user token can fit."""
    with use_local_tokenizers() as tokenizer, pytest.raises(ValueError, match="prompt exceeds exact context budget"):
        fit_prompt_to_budget(_budget_request("echo", 1, static_prefix=OVERSIZED_PREFIX), tokenizer)


def test_budget_keeps_punctuation() -> None:
    """Test user-token capping preserves tokenizer-aware punctuation."""
    with use_punctuation_aware_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(
            _budget_request(
                "remind me: passport, charger, adapters!",
                PUNCTUATION_FIT_LIMIT,
                maximum_user_tokens=4,
            ),
            tokenizer,
        )

        assert fit.history_messages == []
        assert fit.user_utterance == "remind me: passport"
        assert fit.prompt_tokens <= PUNCTUATION_FIT_LIMIT
