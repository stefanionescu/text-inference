"""History orchestration for SessionState storage."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from src.session.state import SessionState, HistoryMessage

from .transcript import trim_history, format_history

if TYPE_CHECKING:
    from src.runtime.config import HistorySettings
    from src.tokens.tokenizer import ThreadSafeTokenizer


def _normalize_role(role: str) -> Literal["user", "assistant"] | None:
    """Return a canonical stored history role or None.

    Args:
        role: Chat role of the message.

    Returns:
        A canonical stored history role or None.

    """
    if role == "user":
        return "user"
    if role == "assistant":
        return "assistant"
    return None


class HistoryController:
    """History operations for SessionState."""

    def __init__(
        self,
        *,
        config: HistorySettings,
        tokenizer: ThreadSafeTokenizer,
    ) -> None:
        """Initialize history handling dependencies.

        Args:
            config: Settings for this run.
            tokenizer: Tokenizer to use.

        """
        self._config = config
        self._tokenizer = tokenizer

    def _history_messages(self, state: SessionState) -> list[HistoryMessage]:
        """Return mutable history storage for a session.

        Args:
            state: State of the session or test run.

        Returns:
            Mutable history storage for a session.

        """
        messages = state.history_messages
        if messages is None:
            messages = []
            state.history_messages = messages
        return messages

    def _trim_store_eager(
        self,
        state: SessionState,
        *,
        is_import_mode: bool = False,
    ) -> None:
        """Trim stored history immediately after mutation.

        Args:
            state: State of the session or test run.
            is_import_mode: Whether import is mode.

        """
        if is_import_mode:
            trim_history(
                state,
                config=self._config,
                tokenizer=self._tokenizer,
                trigger_tokens=self._config.target_tokens,
            )
            return
        trim_history(
            state,
            config=self._config,
            tokenizer=self._tokenizer,
        )

    def _append_message_to_list(self, messages: list[HistoryMessage], role: str, content: str) -> None:
        """Append normalized content to a history list.

        Args:
            messages: Messages of the conversation.
            role: Chat role of the message.
            content: Text content of the message.

        """
        normalized_content = (content or "").strip()
        normalized_role = _normalize_role(role)
        if normalized_role is None or not normalized_content:
            return
        if normalized_role == "user" and messages and messages[-1].role == "user":
            messages[-1].content = f"{messages[-1].content}\n\n{normalized_content}"
            return
        messages.append(HistoryMessage(role=normalized_role, content=normalized_content))

    def _build_imported_messages(self, history_messages: list[HistoryMessage] | None) -> list[HistoryMessage]:
        """Normalize imported history messages.

        Args:
            history_messages: History messages.

        Returns:
            The updated value.

        """
        normalized_history_messages: list[HistoryMessage] = []
        for message in history_messages or []:
            self._append_message_to_list(normalized_history_messages, message.role, message.content)
        return normalized_history_messages

    def get_messages(self, state: SessionState) -> list[HistoryMessage]:
        """Get a copy of committed history messages.

        Args:
            state: State of the session or test run.

        Returns:
            A copy of committed history messages.

        """
        messages = self._history_messages(state)
        copied_messages = [HistoryMessage(role=message.role, content=message.content) for message in messages]
        if not copied_messages:
            return []
        return copied_messages

    def set_mode_histories(
        self,
        state: SessionState,
        *,
        history_messages: list[HistoryMessage] | None = None,
    ) -> str:
        """Set imported history and apply import-time trimming.

        Args:
            state: State of the session or test run.
            history_messages: History messages.

        Returns:
            The resulting text.

        """
        normalized_history_messages = self._build_imported_messages(history_messages)
        state.history_messages = normalized_history_messages
        self._trim_store_eager(state, is_import_mode=True)
        return format_history(self._history_messages(state))

    def append_response(
        self,
        state: SessionState,
        user_utterance: str,
        assistant_text: str,
    ) -> str:
        """Append one response as stored user+assistant messages.

        Args:
            state: State of the session or test run.
            user_utterance: User utterance.
            assistant_text: Text of the assistant.

        Returns:
            The resulting text.

        """
        user = (user_utterance or "").strip()
        assistant = (assistant_text or "").strip()
        if not user:
            return format_history(self._history_messages(state))

        self._append_message_to_list(self._history_messages(state), "user", user)
        if assistant:
            self._append_message_to_list(self._history_messages(state), "assistant", assistant)
        self._trim_store_eager(state)
        return format_history(self._history_messages(state))


__all__ = ["HistoryController"]
