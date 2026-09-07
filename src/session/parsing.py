"""History parsing utilities for converting client payloads into runtime state."""

from __future__ import annotations

from src.state.session import HistoryMessage
from typing import TYPE_CHECKING, Literal, cast

if TYPE_CHECKING:
    from collections.abc import Sequence


def _validate_message_item(item: object) -> tuple[str, str] | None:
    """Validate one client history item and return ``(role, content)``."""
    if not isinstance(item, dict):
        return None
    mapping = cast("dict[object, object]", item)
    role = mapping.get("role")
    content = mapping.get("content")
    if not isinstance(role, str) or not isinstance(content, str):
        return None
    normalized_role = role.strip().lower()
    normalized_content = content.strip()
    if not normalized_role or not normalized_content:
        return None
    return normalized_role, normalized_content


def _normalize_role(role: str) -> Literal["user", "assistant"] | None:
    """Return a supported history role or None."""
    if role == "user":
        return "user"
    if role == "assistant":
        return "assistant"
    return None


def _append_message(messages: list[HistoryMessage], role: str, content: str) -> None:
    """Append a normalized history message, merging adjacent user turns."""
    normalized_content = content.strip()
    normalized_role = _normalize_role(role)
    if normalized_role is None or not normalized_content:
        return
    if normalized_role == "user" and messages and messages[-1].role == "user":
        messages[-1].content = f"{messages[-1].content}\n\n{normalized_content}"
        return
    messages.append(HistoryMessage(role=normalized_role, content=normalized_content))


def _split_transcript_line(line: str) -> tuple[str, str] | None:
    """Split a role-prefixed transcript line into role and content."""
    if line.startswith("User:"):
        return "user", line[5:].lstrip()
    if line.startswith("Assistant:"):
        return "assistant", line[10:].lstrip()
    return None


def parse_history_text(history_text: str) -> list[HistoryMessage]:
    """Parse a transcript string back into canonical messages."""
    text = (history_text or "").strip()
    if not text:
        return []

    messages: list[HistoryMessage] = []
    current_role: str | None = None
    current_lines: list[str] = []

    def _flush() -> None:
        """Commit the current transcript block to parsed messages."""
        nonlocal current_role, current_lines
        if current_role is None or not current_lines:
            current_role = None
            current_lines = []
            return
        _append_message(messages, current_role, "\n".join(current_lines).strip())
        current_role = None
        current_lines = []

    for line in text.splitlines():
        marker = _split_transcript_line(line)
        if marker is not None:
            role, content = marker
            _flush()
            current_role = role
            current_lines = [content]
        elif current_role is not None:
            current_lines.append(line)
        elif line.strip():
            current_role = "user"
            current_lines = [line]

    _flush()
    return messages


def parse_history_messages(messages: Sequence[object]) -> list[HistoryMessage]:
    """Parse client history into canonical ordered messages."""
    if not messages:
        return []

    parsed: list[HistoryMessage] = []
    for item in messages:
        validated = _validate_message_item(item)
        if validated is None:
            continue
        role, content = validated
        _append_message(parsed, role, content)
    return parsed


def parse_history_as_tuples(history_text: str) -> list[tuple[str, str]]:
    """Convert a transcript string into ``(user, assistant)`` pairs."""
    messages = parse_history_text(history_text)
    pairs: list[tuple[str, str]] = []
    pending_user = ""

    for message in messages:
        if message.role == "user":
            if pending_user:
                pairs.append((pending_user, ""))
            pending_user = message.content
            continue
        if pending_user:
            pairs.append((pending_user, message.content))
            pending_user = ""
        else:
            pairs.append(("", message.content))

    if pending_user:
        pairs.append((pending_user, ""))
    return pairs


__all__ = [
    "parse_history_as_tuples",
    "parse_history_messages",
    "parse_history_text",
]
