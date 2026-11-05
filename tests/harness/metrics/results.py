"""Shared result factories for test utilities.

This module provides factory functions for creating consistent result
dictionaries across all test scripts. Uses BenchmarkMetrics from tests.state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from tests.state.metrics import BenchmarkMetrics


def error_result(
    error: str,
    *,
    phase: int = 1,
    error_code: str | None = None,
    is_recoverable: bool = False,
) -> dict[str, Any]:
    """Create an error result dict with consistent structure.

    Args:
        error: Error text or error object to report.
        phase: Number of the test phase.
        error_code: Code of the error.
        is_recoverable: Whether it is recoverable.

    Returns:
        An error result dict with consistent structure.

    """
    result: dict[str, Any] = {
        "ok": False,
        "error": error,
        "phase": phase,
    }
    if error_code:
        result["error_code"] = error_code
    if is_recoverable:
        result["recoverable"] = is_recoverable
    return result


def success_result(
    *,
    phase: int = 1,
    ttfb_ms: float | None = None,
    first_sentence_ms: float | None = None,
    first_three_words_ms: float | None = None,
) -> dict[str, Any]:
    """Create a success result dict with timing metrics.

    Args:
        phase: Number of the test phase.
        ttfb_ms: First-byte time in milliseconds.
        first_sentence_ms: First sentence in milliseconds.
        first_three_words_ms: First three words in milliseconds.

    Returns:
        A success result dict with timing metrics.

    """
    return {
        "ok": True,
        "phase": phase,
        "ttfb_ms": ttfb_ms,
        "first_sentence_ms": first_sentence_ms,
        "first_three_words_ms": first_three_words_ms,
    }


def result_to_dict(payload: BenchmarkMetrics) -> dict[str, Any]:
    """Convert BenchmarkMetrics to a plain dict representation.

    Args:
        payload: Decoded message fields.

    Returns:
        The updated value.

    """
    result: dict[str, Any] = {"ok": payload.is_successful, "phase": payload.phase}
    if not payload.is_successful:
        result["error"] = payload.error
        if payload.error_code:
            result["error_code"] = payload.error_code
        result["recoverable"] = payload.is_recoverable
    else:
        if payload.ttfb_ms is not None:
            result["ttfb_ms"] = payload.ttfb_ms
        if payload.first_sentence_ms is not None:
            result["first_sentence_ms"] = payload.first_sentence_ms
        if payload.first_three_words_ms is not None:
            result["first_three_words_ms"] = payload.first_three_words_ms
    return result


__all__ = [
    "error_result",
    "result_to_dict",
    "success_result",
]
