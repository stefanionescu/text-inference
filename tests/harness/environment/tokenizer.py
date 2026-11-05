"""Shared local tokenizer setup for CPU-only unit tests."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING
from functools import lru_cache
from contextlib import contextmanager
from dataclasses import field, dataclass

from src.tokens.tokenizer import ThreadSafeTokenizer
from config.tests.tokenizer import TEST_TOKENIZER_VOCAB

if TYPE_CHECKING:
    from collections.abc import Generator


@dataclass
class _FakeTransformersTokenizer:
    _vocab: dict[str, int]
    _reverse_vocab: dict[int, str] = field(init=False)
    _unk_id: int = field(init=False)

    def __post_init__(self) -> None:
        """Build reverse lookup tables."""
        self._reverse_vocab = {index: token for token, index in self._vocab.items()}
        self._unk_id = self._vocab["[UNK]"]

    def encode(self, text: str, *, add_special_tokens: bool = False) -> list[int]:
        _ = add_special_tokens
        tokens = text.split()
        return [self._vocab.get(token, self._unk_id) for token in tokens]

    def __call__(
        self,
        text: str,
        *,
        add_special_tokens: bool = False,
        return_attention_mask: bool = False,
        return_token_type_ids: bool = False,
    ) -> dict[str, list[int]]:
        _ = return_attention_mask
        _ = return_token_type_ids
        return {"input_ids": self.encode(text, add_special_tokens=add_special_tokens)}

    def decode(
        self,
        ids: list[int],
        *,
        skip_special_tokens: bool = True,
        clean_up_tokenization_spaces: bool = False,
    ) -> str:
        _ = skip_special_tokens
        _ = clean_up_tokenization_spaces
        tokens = [self._reverse_vocab.get(token_id, "[UNK]") for token_id in ids]
        separator = " "
        return separator.join(tokens)


@dataclass
class _StaticTokenizer(ThreadSafeTokenizer):
    _tokenizer: _FakeTransformersTokenizer

    def count(self, text: str, *, are_special_tokens_added: bool = False) -> int:
        has_text = bool(text)
        if not has_text and not are_special_tokens_added:
            return 0
        return len(self.encode_ids(text))

    def trim(self, text: str, maximum_tokens: int, retained_side: str = "end") -> str:
        if maximum_tokens <= 0 or not text:
            return ""
        token_ids = self.encode_ids(text)
        if len(token_ids) <= maximum_tokens:
            return text
        retained_token_ids = token_ids[:maximum_tokens] if retained_side == "start" else token_ids[-maximum_tokens:]
        return self._tokenizer.decode(
            retained_token_ids,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False,
        )

    def encode_ids(self, text: str) -> list[int]:
        if not text:
            return []
        are_special_tokens_added = False
        return self._tokenizer.encode(text, add_special_tokens=are_special_tokens_added)

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        is_generation_prompt_added: bool = True,
        **_template_options: object,
    ) -> str:
        lines: list[str] = []
        for message in messages:
            lines.extend([f"<|im_start|>{message['role']}", message["content"], "<|im_end|>"])
        if is_generation_prompt_added:
            lines.append("<|im_start|>assistant")
        return "\n".join(lines)


_PUNCT_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9]+(?:'[A-Za-z0-9]+)?|[^\w\s]", re.UNICODE)
_ATTACHED_PUNCT = {".", ",", "!", "?", ";", ":", "%", ")", "]", "}"}
_OPENING_PUNCT = {"(", "[", "{", "/", "$", "#"}


@dataclass
class _PunctuationAwareTokenizer(ThreadSafeTokenizer):
    _vocab: dict[str, int] = field(init=False)
    _reverse_vocab: dict[int, str] = field(init=False)
    _next_id: int = field(init=False)

    def __post_init__(self) -> None:
        """Initialize punctuation-aware vocabulary state."""
        self._vocab = {"[BOS]": 0, "[EOS]": 1}
        self._reverse_vocab = {0: "[BOS]", 1: "[EOS]"}
        self._next_id = 2

    def _tokenize(self, text: str) -> list[str]:
        pattern = _PUNCT_TOKEN_PATTERN
        source = text
        return pattern.findall(source)

    def _token_id(self, token: str) -> int:
        token_id = self._vocab.get(token)
        if token_id is None:
            token_id = self._next_id
            self._next_id += 1
            self._vocab[token] = token_id
            self._reverse_vocab[token_id] = token
        return token_id

    def _decode_tokens(self, tokens: list[str]) -> str:
        if not tokens:
            return ""

        output_text = tokens[0]
        for token in tokens[1:]:
            if token in _ATTACHED_PUNCT or output_text[-1] in _OPENING_PUNCT:
                output_text += token
            else:
                output_text += f" {token}"
        return output_text

    def count(self, text: str, *, are_special_tokens_added: bool = False) -> int:
        token_count = len(self._tokenize(text))
        if are_special_tokens_added:
            return token_count + 2
        return token_count

    def trim(self, text: str, maximum_tokens: int, retained_side: str = "end") -> str:
        if maximum_tokens <= 0 or not text:
            return ""
        tokens = self._tokenize(text)
        if len(tokens) <= maximum_tokens:
            return text.strip()
        retained_tokens = tokens[:maximum_tokens] if retained_side == "start" else tokens[-maximum_tokens:]
        return self._decode_tokens(retained_tokens)

    def encode_ids(self, text: str) -> list[int]:
        tokens = self._tokenize(text)
        return [self._token_id(token) for token in tokens]

    def apply_chat_template(
        self,
        messages: list[dict[str, str]],
        *,
        is_generation_prompt_added: bool = True,
        **_template_options: object,
    ) -> str:
        lines: list[str] = []
        for message in messages:
            lines.extend([f"<|im_start|>{message['role']}", message["content"], "<|im_end|>"])
        if is_generation_prompt_added:
            lines.append("<|im_start|>assistant")
        return "\n".join(lines)


@lru_cache(maxsize=1)
def _build_test_tokenizer() -> ThreadSafeTokenizer:
    vocab_size = len(TEST_TOKENIZER_VOCAB)
    if vocab_size <= 0:
        raise ValueError
    transformers_tokenizer = _FakeTransformersTokenizer(TEST_TOKENIZER_VOCAB)
    return _StaticTokenizer(transformers_tokenizer)


def build_local_tokenizer() -> ThreadSafeTokenizer:
    """Return the deterministic unit-test tokenizer."""
    return _build_test_tokenizer()


@contextmanager
def use_local_tokenizers() -> Generator[ThreadSafeTokenizer, None, None]:
    """Yield the deterministic local tokenizer."""
    yield build_local_tokenizer()


@contextmanager
def use_punctuation_aware_tokenizers() -> Generator[_PunctuationAwareTokenizer, None, None]:
    """Yield a punctuation-aware tokenizer."""
    yield _PunctuationAwareTokenizer()
