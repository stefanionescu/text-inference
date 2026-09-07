"""Thread-safe Transformers tokenizer adapter."""

from __future__ import annotations

import os
from threading import Lock
from transformers import AutoTokenizer
from typing import TYPE_CHECKING, Protocol, cast
from src.tokens.validation import require_local_model_directory

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

# Disable tokenizers parallelism before importing transformers/tokenizers.
os.environ["TOKENIZERS_PARALLELISM"] = "false"


class _Tokenizer(Protocol):
    """Transformers tokenizer behavior used by the local adapter."""

    def __call__(
        self,
        text: str,
        *,
        add_special_tokens: bool,
        return_attention_mask: bool,
        return_token_type_ids: bool,
    ) -> Mapping[str, object]:
        """Encode text into tokenizer fields."""
        raise NotImplementedError(
            text,
            add_special_tokens,
            return_attention_mask,
            return_token_type_ids,
        )

    def decode(
        self,
        token_ids: list[int],
        *,
        skip_special_tokens: bool,
        clean_up_tokenization_spaces: bool,
    ) -> str:
        """Decode token identifiers into text."""
        raise NotImplementedError(
            token_ids,
            skip_special_tokens,
            clean_up_tokenization_spaces,
        )

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        tokenize: bool,
        add_generation_prompt: bool,
        **template_options: object,
    ) -> object:
        """Apply a tokenizer-owned chat template."""
        raise NotImplementedError(
            messages,
            tokenize,
            add_generation_prompt,
            template_options,
        )


class ThreadSafeTokenizer:
    """Thread-safe adapter around one Transformers tokenizer."""

    def __init__(self, model_directory: str) -> None:
        """Initialize a tokenizer from an existing local model directory."""
        self._lock = Lock()
        model_path = require_local_model_directory(model_directory)
        create_tokenizer: Callable[..., _Tokenizer] = cast(
            "Callable[..., _Tokenizer]",
            AutoTokenizer.from_pretrained,
        )
        self._tokenizer = create_tokenizer(
            model_path,
            trust_remote_code=True,
            local_files_only=True,
        )

    def _encode_token_ids_locked(
        self,
        text: str,
        *,
        are_special_tokens_added: bool = False,
    ) -> list[int]:
        """Encode text with optional special tokens.

        Must be called while holding ``self._lock``.
        """
        encoded_input = self._tokenizer(
            text,
            add_special_tokens=are_special_tokens_added,
            return_attention_mask=False,
            return_token_type_ids=False,
        )
        return cast("list[int]", encoded_input["input_ids"])

    def count(self, text: str, *, are_special_tokens_added: bool = False) -> int:
        """Count the number of tokens in the text.

        Args:
            text: Text to tokenize and count.
            are_special_tokens_added: Whether to include tokenizer-added special tokens.

        Returns:
            Number of tokens in the text.

        """
        source_text = text
        if not source_text and not are_special_tokens_added:
            return 0
        with self._lock:
            return len(
                self._encode_token_ids_locked(
                    source_text,
                    are_special_tokens_added=are_special_tokens_added,
                ),
            )

    def trim(self, text: str, maximum_tokens: int, retained_side: str = "end") -> str:
        """Trim text to fit within the token limit.

        Args:
            text: Text to trim.
            maximum_tokens: Maximum number of tokens to keep.
            retained_side: Which part to keep: ``start`` or ``end``.

        Returns:
            Trimmed text fitting within the token limit.

        """
        retention_side = retained_side
        if maximum_tokens <= 0 or not text:
            return ""
        with self._lock:
            token_ids = self._encode_token_ids_locked(text)
            if len(token_ids) <= maximum_tokens:
                return text
            retained_token_ids = (
                token_ids[:maximum_tokens] if retention_side == "start" else token_ids[-maximum_tokens:]
            )
            return self._tokenizer.decode(
                retained_token_ids,
                skip_special_tokens=True,
                clean_up_tokenization_spaces=False,
            )

    def encode_ids(self, text: str) -> list[int]:
        """Return token ids for the provided text without special tokens.

        Args:
            text: Text to encode.

        Returns:
            List of token IDs.

        """
        source_text = text
        if not source_text:
            return []
        with self._lock:
            return self._encode_token_ids_locked(source_text)

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        is_generation_prompt_added: bool = True,
        **template_options: object,
    ) -> str:
        """Apply the tokenizer's built-in chat template to format messages.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
                      Roles are typically 'system', 'user', 'assistant'.
            is_generation_prompt_added: Whether to append the assistant turn start token.
            **template_options: Additional options passed to the provider template.

        Returns:
            Formatted prompt string ready for generation.

        Raises:
            RuntimeError: If tokenizer has no chat template support.

        """
        with self._lock:
            formatted_prompt = self._tokenizer.apply_chat_template(
                messages,
                tokenize=False,
                add_generation_prompt=is_generation_prompt_added,
                **template_options,
            )
            return str(formatted_prompt)


__all__ = ["ThreadSafeTokenizer"]
