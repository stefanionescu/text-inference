"""Streaming sanitizer regression cases."""

from __future__ import annotations

import json
from typing import cast
from pathlib import Path

_EXAMPLE_PATH = Path(__file__).with_name("examples") / "streaming_sanitizer_cases.json"
CASE_ITEM_WIDTH = 2


def _read_cases() -> list[tuple[str, list[int]]]:
    """Load streaming sanitizer cases from JSON fixture examples.

    Returns:
        Streaming sanitizer cases from JSON fixture examples.

    Raises:
        TypeError: Streaming sanitizer fixture must be a list.

    """
    raw: object = json.loads(_EXAMPLE_PATH.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        message = "streaming sanitizer fixture must be a list"
        raise TypeError(message)
    entries = cast("list[object]", raw)
    cases: list[tuple[str, list[int]]] = []
    for item in entries:
        if not isinstance(item, list | tuple):
            message = "streaming sanitizer entries must be [text, splits]"
            raise TypeError(message)
        entry = cast("list[object] | tuple[object, ...]", item)
        if len(entry) != CASE_ITEM_WIDTH:
            message = "streaming sanitizer entries must be [text, splits]"
            raise TypeError(message)
        text, splits = entry
        if not isinstance(text, str) or not isinstance(splits, list):
            message = "streaming sanitizer entries require text and split list"
            raise TypeError(message)
        split_values = cast("list[object]", splits)
        if any(isinstance(split, bool) or not isinstance(split, int) for split in split_values):
            message = "streaming sanitizer split values must be integers"
            raise TypeError(message)
        cases.append((text, cast("list[int]", split_values)))
    return cases


STREAMING_SANITIZER_CASES = _read_cases()

__all__ = ["STREAMING_SANITIZER_CASES"]
