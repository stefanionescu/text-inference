"""Session configuration update logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.state.session import SessionState


def update_session_config(
    state: SessionState,
    *,
    gender: str | None = None,
    personality: str | None = None,
    prompt: str | None = None,
    sampling: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Update mutable prompt and profile configuration for a session.

    Only fields that are explicitly provided (not None) are updated.
    Other fields retain their current values.

    Args:
        state: The session state to update.
        gender: New gender value, if provided.
        personality: New personality (will be lowercased), if provided.
        prompt: New custom system prompt, if provided.
        sampling: New sampling parameters dict, if provided.

    Returns:
        Dict of field names to their new values (only changed fields).

    """
    meta = state.meta
    changed: dict[str, Any] = {}

    if gender is not None:
        meta["gender"] = gender
        changed["gender"] = gender

    if personality is not None:
        meta["personality"] = personality or None
        changed["personality"] = personality or None

    if prompt is not None:
        profile_prompt = prompt or None
        meta["prompt"] = profile_prompt
        changed["prompt"] = bool(profile_prompt)

    if sampling is not None:
        normalized_sampling = sampling or None
        sampling_copy = normalized_sampling.copy() if isinstance(normalized_sampling, dict) else None
        meta["sampling"] = sampling_copy
        changed["sampling"] = sampling_copy.copy() if isinstance(sampling_copy, dict) else None

    return changed


__all__ = ["update_session_config"]
