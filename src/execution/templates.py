"""Prompt construction using tokenizer templates."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING
from config.prompt.templates import IS_TEMPLATE_THINKING_ENABLED

if TYPE_CHECKING:
    from collections.abc import Sequence
    from src.session.state import HistoryMessage
    from src.tokens.tokenizer import ThreadSafeTokenizer


def _is_template_thinking_enabled() -> bool:
    """Return the template thinking flag without importing runtime helpers."""
    value = os.getenv("TEMPLATE_ENABLE_THINKING")
    if value is None:
        return IS_TEMPLATE_THINKING_ENABLED
    if value == "1":
        return True
    if value == "0":
        return False
    message = "TEMPLATE_ENABLE_THINKING must be 0 or 1"
    raise ValueError(message)


_TEMPLATE_DEFAULT_OPTIONS = {"enable_thinking": _is_template_thinking_enabled()}


def _build_messages(
    system_prompt: str,
    history_messages: Sequence[HistoryMessage],
    user_utterance: str | None,
) -> list[dict[str, str]]:
    """Build message dicts for the tokenizer template."""
    messages: list[dict[str, str]] = []

    def _append_message(role: str, content: str) -> None:
        """Append non-empty content, merging consecutive same-role messages."""
        content = content.strip()
        if not content:
            return
        if messages and messages[-1]["role"] == role:
            messages[-1]["content"] += "\n\n" + content
            return
        messages.append({"role": role, "content": content})

    if system_prompt.strip():
        messages.append({"role": "system", "content": system_prompt.strip()})

    for message in history_messages:
        _append_message(message.role, message.content)

    if user_utterance is not None:
        _append_message("user", user_utterance)

    return messages


def _compose_system_prompt(static_prefix: str, runtime_text: str) -> str:
    """Join static and runtime system prompt text."""
    parts = [segment.strip() for segment in (static_prefix, runtime_text) if segment and segment.strip()]
    return "\n\n".join(parts)


def build_prefixed_prompt(
    static_prefix: str,
    runtime_text: str,
    history_messages: list[HistoryMessage],
    user_utterance: str,
    tokenizer: ThreadSafeTokenizer,
) -> str:
    """Build a prompt including the current user turn."""
    system_prompt = _compose_system_prompt(static_prefix, runtime_text)
    messages = _build_messages(system_prompt, history_messages, user_utterance)
    return tokenizer.apply_chat_template(
        messages,
        is_generation_prompt_added=True,
        **_TEMPLATE_DEFAULT_OPTIONS,
    )


__all__ = ["build_prefixed_prompt"]
