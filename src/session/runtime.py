"""Session handler orchestration logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.execution.budget import PromptBudgetRequest, fit_prompt_to_budget

from .time import format_session_timestamp
from .history.controller import HistoryController

if TYPE_CHECKING:
    from src.session.state import SessionState, HistoryMessage
    from src.runtime.config import ApplicationSettings
    from src.tokens.tokenizer import ThreadSafeTokenizer


class SessionRuntime:
    """Stateless helper for session metadata, request tracking, and lifecycle.

    Methods operate on a SessionState passed by the caller (per-connection).
    It holds no session dict or eviction logic, because each connection owns its session.
    """

    def __init__(
        self,
        *,
        tokenizer: ThreadSafeTokenizer,
        settings: ApplicationSettings,
    ) -> None:
        """Initialize the session services with resolved startup settings.

        Args:
            tokenizer: Tokenizer to use.
            settings: Application settings.

        """
        self.tokenizer = tokenizer
        self.history_config = settings.history
        self.session_settings = settings.session
        self.model_settings = settings.model
        self.sampling_settings = settings.sampling
        self.history = HistoryController(
            config=self.history_config,
            tokenizer=tokenizer,
        )

    # ============================================================================
    # Session metadata / lifecycle
    # ============================================================================

    def initialize_session(self, state: SessionState) -> dict[str, Any]:
        """Populate a fresh session state with default metadata.

        Args:
            state: State of the session or test run.

        Returns:
            The resulting mapping.

        """
        if state.history_messages is None:
            state.history_messages = []
        timestamp = format_session_timestamp()
        meta = state.meta
        meta.update(
            {
                "now_iso": timestamp.iso_timestamp,
                "now_str": timestamp.display,
                "now_classification": timestamp.classification,
                "now_tz": timestamp.timezone_name,
                "gender": None,
                "personality": None,
                "prompt": None,
                "sampling": None,
                "model": self.model_settings.source,
            },
        )
        return meta

    def fit_start_history(
        self,
        state: SessionState,
        *,
        static_prefix: str,
        runtime_text: str = "",
    ) -> list[HistoryMessage]:
        """Exact-fit seeded history at start time and reject impossible latest turns.

        Args:
            state: State of the session or test run.
            static_prefix: Static prefix.
            runtime_text: Text of the runtime.

        Returns:
            The resulting items.

        Raises:
            ValueError: Seed history exceeds exact context budget at session start.

        """
        original_history = self.history.get_messages(state)
        if not original_history:
            return []

        prompt_fit = fit_prompt_to_budget(
            PromptBudgetRequest(
                static_prefix=static_prefix,
                runtime_text=runtime_text,
                history_messages=original_history,
                user_utterance="",
                maximum_prompt_tokens=self.session_settings.maximum_context_length,
            ),
            self.tokenizer,
        )
        if prompt_fit.history_messages:
            state.history_messages = prompt_fit.history_messages
            return prompt_fit.history_messages

        message = "seed history exceeds exact context budget at session start"
        raise ValueError(message)


__all__ = ["SessionRuntime"]
