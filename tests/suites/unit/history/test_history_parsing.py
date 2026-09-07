"""Unit tests for history parsing helpers."""

from __future__ import annotations

from tests.harness.messages.unit import ASSISTANT_FIRST_MESSAGES, ASSISTANT_FIRST_PAYLOAD
from src.session.parsing import parse_history_as_tuples, parse_history_messages, parse_history_text


def test_parse_multiline() -> None:
    """Test parse history text preserves multiline sections."""
    history_text = (
        "User: hello can you help me plan a trip\n"
        "Assistant: sure tell me your budget\n"
        "and hotel area\n"
        "User: i need a quiet hotel\n"
        "near the river\n"
        "Assistant: great"
    )

    messages = parse_history_text(history_text)

    assert [(message.role, message.content) for message in messages] == [
        ("user", "hello can you help me plan a trip"),
        ("assistant", "sure tell me your budget\nand hotel area"),
        ("user", "i need a quiet hotel\nnear the river"),
        ("assistant", "great"),
    ]


def test_tuple_order() -> None:
    """Test parse history as tuples returns ordered pairs."""
    history_text = (
        "User: hello can you help me plan a trip\n"
        "Assistant: sure tell me your budget\n"
        "User: i need a quiet hotel near the river\n"
        "Assistant: great"
    )

    parsed = parse_history_as_tuples(history_text)

    assert parsed == [
        ("hello can you help me plan a trip", "sure tell me your budget"),
        ("i need a quiet hotel near the river", "great"),
    ]


def test_tuple_leading_assistants() -> None:
    """Test parse history as tuples preserves leading assistant sections."""
    history_text = (
        "Assistant: hello can you help me plan a trip to lisbon next week\n"
        "Assistant: sure tell me your budget and hotel area preference\n"
        "User: i need a quiet hotel near the river and my budget is moderate\n"
        "Assistant: a quiet riverside hotel in lisbon can work and i can suggest neighborhoods\n"
        "User: also remind me to pack a rain jacket and travel adapter\n"
        "Assistant: i will keep weather and transit options in mind for that trip"
    )

    parsed = parse_history_as_tuples(history_text)

    assert parsed == [
        ("", "hello can you help me plan a trip to lisbon next week"),
        ("", "sure tell me your budget and hotel area preference"),
        (
            "i need a quiet hotel near the river and my budget is moderate",
            "a quiet riverside hotel in lisbon can work and i can suggest neighborhoods",
        ),
        (
            "also remind me to pack a rain jacket and travel adapter",
            "i will keep weather and transit options in mind for that trip",
        ),
    ]


def test_consecutive_users_merge() -> None:
    """Test consecutive users combined."""
    messages = [
        {"role": "user", "content": "hello can you help me plan a trip"},
        {"role": "user", "content": "i need a quiet hotel near the river"},
        {"role": "assistant", "content": "sure tell me your budget"},
    ]
    parsed = parse_history_messages(messages)
    assert [(message.role, message.content) for message in parsed] == [
        ("user", "hello can you help me plan a trip\n\ni need a quiet hotel near the river"),
        ("assistant", "sure tell me your budget"),
    ]


def test_consecutive_assistants_split() -> None:
    """Test consecutive assistants not combined."""
    messages = [
        {"role": "user", "content": "hello can you help me plan a trip"},
        {"role": "assistant", "content": "sure tell me your budget"},
        {"role": "assistant", "content": "and hotel area"},
    ]
    parsed = parse_history_messages(messages)
    assert [(message.role, message.content) for message in parsed] == [
        ("user", "hello can you help me plan a trip"),
        ("assistant", "sure tell me your budget"),
        ("assistant", "and hotel area"),
    ]


def test_assistant_first_order() -> None:
    """Test preserves assistant first history in order."""
    parsed = parse_history_messages(ASSISTANT_FIRST_PAYLOAD)

    assert parsed == ASSISTANT_FIRST_MESSAGES


def test_drops_unknown_roles() -> None:
    """Test drops non user assistant roles."""
    messages = [
        {"role": "system", "content": "sys"},
        {"role": "user", "content": "u1"},
        {"role": "function", "content": "fn"},
        {"role": "assistant", "content": "a1"},
    ]
    parsed = parse_history_messages(messages)
    assert [(message.role, message.content) for message in parsed] == [("user", "u1"), ("assistant", "a1")]


def test_validates_items() -> None:
    """Test validates items."""
    messages = [
        42,
        {"role": "user"},
        {"content": "no role"},
        {"role": "user", "content": "valid"},
        {"role": "assistant", "content": "reply"},
    ]
    parsed = parse_history_messages(messages)
    assert [(message.role, message.content) for message in parsed] == [("user", "valid"), ("assistant", "reply")]


def test_trailing_user_message() -> None:
    """Test trailing user preserved as user message."""
    messages = [
        {"role": "user", "content": "u1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "u2"},
    ]
    parsed = parse_history_messages(messages)
    assert [(message.role, message.content) for message in parsed] == [
        ("user", "u1"),
        ("assistant", "a1"),
        ("user", "u2"),
    ]


def test_empty_list() -> None:
    """Test empty list."""
    assert parse_history_messages([]) == []
