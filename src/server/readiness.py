"""Server readiness state."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class ReadinessState:
    """Track runtime initialization, public acceptance, and draining.

    Attributes:
        is_runtime_initialized: Whether runtime is initialized.
        is_public_accepting: Whether public is accepting.
        is_draining: Whether it is draining.

    """

    is_runtime_initialized: bool = False
    is_public_accepting: bool = False
    is_draining: bool = False

    @property
    def is_ready(self) -> bool:
        """Return whether the public service can accept inference traffic."""
        return self.is_runtime_initialized and self.is_public_accepting and not self.is_draining

    def start_initializing(self) -> None:
        """Reset status before runtime dependency initialization."""
        self.is_runtime_initialized = False
        self.is_public_accepting = False
        self.is_draining = False

    def start_draining(self) -> None:
        """Make readiness fail before runtime resources begin draining."""
        self.is_runtime_initialized = False
        self.is_draining = True
        self.is_public_accepting = False


__all__ = ["ReadinessState"]
