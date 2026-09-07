"""Session handler orchestration logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from .time import format_session_timestamp
from src.state.execution import PromptBudgetRequest
from src.execution.budget import fit_prompt_to_budget
from .history import HistoryController, build_history_runtime_config
from .defaults import DEFAULT_MODEL_SETTINGS, DEFAULT_SAMPLING_SETTINGS, DEFAULT_SESSION_SETTINGS
from .requests import (
    cancel_session_requests,
    cleanup_session_requests,
)

if TYPE_CHECKING:
    from src.engines.protocol import Engine
    from src.tokens.tokenizer import ThreadSafeTokenizer
    from src.state.session import HistoryMessage, SessionState
    from src.state.settings import ApplicationSettings, HistorySettings


class SessionRuntime:
    """Stateless helper for session metadata, request tracking, and lifecycle.

    Methods operate on a SessionState passed by the caller (per-connection).
    No internal session dict or eviction logic — the connection IS the session.
    """

    def __init__(
        self,
        *,
        tokenizer: ThreadSafeTokenizer,
        engine: Engine,
        settings: ApplicationSettings | None = None,
        history_config: HistorySettings | None = None,
    ) -> None:
        """Initialize runtime dependency defaults."""
        self._engine = engine
        self.tokenizer = tokenizer
        self.history_config = history_config or (
            settings.history if settings is not None else build_history_runtime_config()
        )
        self.session_settings = settings.session if settings is not None else DEFAULT_SESSION_SETTINGS
        self.model_settings = settings.model if settings is not None else DEFAULT_MODEL_SETTINGS
        self.sampling_settings = settings.sampling if settings is not None else DEFAULT_SAMPLING_SETTINGS
        self.history = HistoryController(
            config=self.history_config,
            tokenizer=tokenizer,
        )

    # ============================================================================
    # Session metadata / lifecycle
    # ============================================================================

    def initialize_session(self, state: SessionState) -> dict[str, Any]:
        """Populate a fresh session state with default metadata."""
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
        """Exact-fit seeded history at start time and reject impossible latest turns."""
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

    async def abort_session_requests(
        self,
        state: SessionState | None,
    ) -> dict[str, str]:
        """Cancel tracked requests and abort active engine work."""
        if not state:
            return {"active": ""}

        active_request_id = state.active_request_id or ""
        async with state.request_lock:
            cancel_session_requests(state)
        if active_request_id:
            await self._engine.abort(active_request_id)

        async with state.request_lock:
            return cleanup_session_requests(state, is_forced=True)


__all__ = ["SessionRuntime"]
