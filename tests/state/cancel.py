"""Result types for cancel test phases and clients."""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass


@dataclass
class CancelPhaseResult:
    """Result from the cancel phase of the test.

    Attributes:
        has_passed: Whether it passed.
        is_cancelled: Whether it is cancelled.
        tokens_received: Tokens received.
        chars_received: Chars received.
        error: Error text or error object to report.

    """

    has_passed: bool
    is_cancelled: bool
    tokens_received: int
    chars_received: int
    error: str | None = None


@dataclass
class DrainPhaseResult:
    """Result from the drain phase - verifying no spurious messages.

    Attributes:
        has_passed: Whether it passed.
        spurious_messages: Spurious messages.
        error: Error text or error object to report.

    """

    has_passed: bool
    spurious_messages: int
    error: str | None = None


@dataclass
class RecoveryPhaseResult:
    """Result from the recovery phase of the test.

    Attributes:
        has_passed: Whether it passed.
        response_text: Text of the response.
        metrics: Timing metrics of the request.
        error: Error text or error object to report.

    """

    has_passed: bool
    response_text: str
    metrics: dict[str, Any]
    error: str | None = None


@dataclass
class CancelClientResult:
    """Combined result for the client that performs cancel.

    Attributes:
        cancel_phase: Cancel phase.
        drain_phase: Drain phase.
        recovery_phase: Recovery phase.

    """

    cancel_phase: CancelPhaseResult
    drain_phase: DrainPhaseResult
    recovery_phase: RecoveryPhaseResult


@dataclass
class NormalClientResult:
    """Result for a client that completes normally without canceling.

    Attributes:
        client_id: ID of the client.
        has_passed: Whether it passed.
        response_text: Text of the response.
        metrics: Timing metrics of the request.
        error: Error text or error object to report.

    """

    client_id: int
    has_passed: bool
    response_text: str
    metrics: dict[str, Any]
    error: str | None = None


__all__ = [
    "CancelClientResult",
    "CancelPhaseResult",
    "DrainPhaseResult",
    "NormalClientResult",
    "RecoveryPhaseResult",
]
