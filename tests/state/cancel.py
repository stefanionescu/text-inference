"""Result types for cancel test phases and clients."""

from __future__ import annotations

from typing import Any
from dataclasses import dataclass


@dataclass
class CancelPhaseResult:
    """Result from the cancel phase of the test."""

    has_passed: bool
    is_cancelled: bool
    tokens_received: int
    chars_received: int
    error: str | None = None


@dataclass
class DrainPhaseResult:
    """Result from the drain phase - verifying no spurious messages."""

    has_passed: bool
    spurious_messages: int
    error: str | None = None


@dataclass
class RecoveryPhaseResult:
    """Result from the recovery phase of the test."""

    has_passed: bool
    response_text: str
    metrics: dict[str, Any]
    error: str | None = None


@dataclass
class CancelClientResult:
    """Combined result for the client that performs cancel."""

    cancel_phase: CancelPhaseResult
    drain_phase: DrainPhaseResult
    recovery_phase: RecoveryPhaseResult

    @property
    def has_all_passed(self) -> bool:
        """Check if all phases passed."""
        return self.cancel_phase.has_passed and self.drain_phase.has_passed and self.recovery_phase.has_passed


@dataclass
class NormalClientResult:
    """Result for a client that completes normally without canceling."""

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
