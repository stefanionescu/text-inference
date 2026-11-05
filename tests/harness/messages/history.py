"""Long conversation history sample for warm history testing."""

from __future__ import annotations

import json
from typing import cast
from pathlib import Path

_EXAMPLE_FOLDER = Path(__file__).with_name("examples")


def _read_warm_history() -> list[dict[str, str]]:
    """Load warm-history messages from JSON fixture examples.

    Returns:
        Warm-history messages from JSON fixture examples.

    Raises:
        TypeError: Warm history fixture must be a list.

    """
    raw: object = json.loads((_EXAMPLE_FOLDER / "warm_history.json").read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        message = "warm history fixture must be a list"
        raise TypeError(message)
    entries = cast("list[object]", raw)
    history: list[dict[str, str]] = []
    for item in entries:
        if not isinstance(item, dict):
            message = "warm history entries must be objects"
            raise TypeError(message)
        record = cast("dict[object, object]", item)
        role = record.get("role")
        content = record.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            message = "warm history entries require string role and content"
            raise TypeError(message)
        history.append({"role": role, "content": content})
    return history


WARM_HISTORY = _read_warm_history()

HISTORY_RECALL_MESSAGES: list[str] = [
    "Wait, what was the very first thing I told you about at the start of our conversation?",
    "Earlier you mentioned a specific tip about when to activate the JR Pass. What was that again?",
    "What did you say about tipping in Japan? I want to make sure I remember correctly.",
    "Remind me what flour brand you recommended for sourdough?",
    "You gave me a specific temperature range for bulk fermentation. What was it?",
    "What was your advice about scoring cold versus warm dough?",
    "Hey I mentioned a coworker earlier who traveled somewhere recently. What was her name and where did she go?",
    "Did I ever mention someone named Jake? What did I say about him?",
]

__all__ = ["HISTORY_RECALL_MESSAGES", "WARM_HISTORY"]
