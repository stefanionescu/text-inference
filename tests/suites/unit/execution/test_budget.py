"""Unit tests for exact prompt budgeting."""

from __future__ import annotations

import pytest

from src.execution.budget import PromptBudgetRequest, fit_prompt_to_budget
from tests.harness.messages.unit import MESSAGES, ASSISTANT_FIRST_MESSAGES
from tests.harness.environment.tokenizer import use_local_tokenizers, use_punctuation_aware_tokenizers

HISTORY_FIT_LIMIT = 70
ASSISTANT_GROUP_LIMIT = 60
TRIM_USER_LIMIT = 5
USER_CAP_FIT_LIMIT = 20
PUNCTUATION_FIT_LIMIT = 100


def test_budget_keeps_history() -> None:
    """Test prompt fitting keeps the newest complete history groups."""
    with use_local_tokenizers() as tokenizer:
        messages = MESSAGES

        fit = fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix="",
                runtime_text="",
                history_messages=messages,
                user_utterance="hello",
                maximum_prompt_tokens=HISTORY_FIT_LIMIT,
            ),
            tokenizer,
        )

        assert fit.history_messages == MESSAGES[-4:]
        assert fit.user_utterance == "hello"
        assert fit.prompt_tokens <= HISTORY_FIT_LIMIT


def test_budget_drops_group() -> None:
    """Test prompt fitting drops an incomplete leading history group."""
    with use_local_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix="",
                runtime_text="",
                history_messages=MESSAGES[:4],
                user_utterance="hello",
                maximum_prompt_tokens=40,
            ),
            tokenizer,
        )

        assert [(message.role, message.content) for message in fit.history_messages] == [
            ("user", "i need a quiet hotel near the river and my budget is moderate"),
            ("assistant", "a quiet riverside hotel in lisbon can work and i can suggest neighborhoods"),
        ]


def test_budget_keeps_assistant() -> None:
    """Test prompt fitting preserves a valid assistant-first history."""
    with use_local_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix="",
                runtime_text="",
                history_messages=ASSISTANT_FIRST_MESSAGES[:4],
                user_utterance="also remind me to pack a rain jacket and travel adapter",
                maximum_prompt_tokens=200,
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
            PromptBudgetRequest(
                static_prefix="",
                runtime_text="",
                history_messages=ASSISTANT_FIRST_MESSAGES,
                user_utterance="hello",
                maximum_prompt_tokens=ASSISTANT_GROUP_LIMIT,
            ),
            tokenizer,
        )

        assert fit.history_messages == ASSISTANT_FIRST_MESSAGES[-2:]
        assert fit.prompt_tokens <= ASSISTANT_GROUP_LIMIT


def test_budget_trims_user() -> None:
    """Test prompt fitting trims user text to the exact token budget."""
    with use_local_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix="",
                runtime_text="",
                history_messages=[],
                user_utterance="hello can you help me plan a trip to lisbon next week",
                maximum_prompt_tokens=TRIM_USER_LIMIT,
            ),
            tokenizer,
        )

        assert fit.history_messages == []
        assert fit.user_utterance == "hello can"
        assert fit.prompt_tokens <= TRIM_USER_LIMIT


def test_budget_rejects_static() -> None:
    """Test prompt fitting rejects a static prompt that exceeds the budget."""
    with use_local_tokenizers() as tokenizer, pytest.raises(ValueError, match="prompt exceeds exact context budget"):
        fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix="alpha bravo charlie delta",
                runtime_text="",
                history_messages=[],
                user_utterance="",
                maximum_prompt_tokens=1,
            ),
            tokenizer,
        )


def test_budget_applies_cap() -> None:
    """Test prompt fitting applies the configured user token cap."""
    with use_local_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix="",
                runtime_text="",
                history_messages=[],
                user_utterance="hello can you help me plan a trip to lisbon next week",
                maximum_prompt_tokens=USER_CAP_FIT_LIMIT,
                maximum_user_tokens=4,
            ),
            tokenizer,
        )

        assert fit.user_utterance == "hello can you help"
        assert fit.prompt_tokens <= USER_CAP_FIT_LIMIT


def test_budget_rejects_user() -> None:
    """Test prompt fitting rejects text when no user token can fit."""
    with use_local_tokenizers() as tokenizer, pytest.raises(ValueError, match="prompt exceeds exact context budget"):
        fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix="alpha bravo charlie delta",
                runtime_text="",
                history_messages=[],
                user_utterance="echo",
                maximum_prompt_tokens=1,
            ),
            tokenizer,
        )


def test_budget_keeps_punctuation() -> None:
    """Test user-token capping preserves tokenizer-aware punctuation."""
    with use_punctuation_aware_tokenizers() as tokenizer:
        fit = fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix="",
                runtime_text="",
                history_messages=[],
                user_utterance="remind me: passport, charger, adapters!",
                maximum_prompt_tokens=PUNCTUATION_FIT_LIMIT,
                maximum_user_tokens=4,
            ),
            tokenizer,
        )

        assert fit.history_messages == []
        assert fit.user_utterance == "remind me: passport"
        assert fit.prompt_tokens <= PUNCTUATION_FIT_LIMIT
