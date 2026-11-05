"""Shared realistic unit-test message samples."""

from __future__ import annotations

from dataclasses import replace

from src.session.state import HistoryMessage

MESSAGES: list[HistoryMessage] = [
    HistoryMessage(
        role="user",
        content="hello can you help me plan a trip to lisbon next week",
    ),
    HistoryMessage(
        role="assistant",
        content="sure tell me your budget and hotel area preference",
    ),
    HistoryMessage(
        role="user",
        content="i need a quiet hotel near the river and my budget is moderate",
    ),
    HistoryMessage(
        role="assistant",
        content="a quiet riverside hotel in lisbon can work and i can suggest neighborhoods",
    ),
    HistoryMessage(
        role="user",
        content="also remind me to pack a rain jacket and travel adapter",
    ),
    HistoryMessage(
        role="assistant",
        content="i will keep weather and transit options in mind for that trip",
    ),
]


HISTORY_PAYLOAD: list[dict[str, str]] = [{"role": message.role, "content": message.content} for message in MESSAGES]


ASSISTANT_FIRST_MESSAGES: list[HistoryMessage] = [
    replace(MESSAGES[0], role="assistant"),
    *(replace(message) for message in MESSAGES[1:]),
]


ASSISTANT_FIRST_PAYLOAD: list[dict[str, str]] = [
    {"role": message.role, "content": message.content} for message in ASSISTANT_FIRST_MESSAGES
]


__all__ = [
    "ASSISTANT_FIRST_MESSAGES",
    "ASSISTANT_FIRST_PAYLOAD",
    "HISTORY_PAYLOAD",
    "MESSAGES",
]
